"""End-to-end v0.1 pipeline: P0 baseline -> P1 distill -> P2 RLCR -> P3 TRIAGE -> P4 HIKMAT days.

With the mock backend this runs on a CPU in under a minute and checks that every stage
moves its metric in the right direction and that the safety gates fire when attacked.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass

import numpy as np

from mycelium.autopilot import Autopilot, GoldenSet, TamperError
from mycelium.distill import distill
from mycelium.evals.datasets import FEATURE_DIM, family_center, make_suite
from mycelium.evals.harness import evaluate
from mycelium.evals.judges import judge
from mycelium.hikmat.codec import CodonCodec
from mycelium.hikmat.memory import HikmatMemory
from mycelium.models.base import ModelBackend
from mycelium.models.cache import CachedBackend
from mycelium.models.mock import MockModel, method_tag
from mycelium.rlcr import learnable_problems, run_rlcr
from mycelium.router import Thresholds, Triage, run_policy, teacher_only, tune_thresholds

# Harder families that keep coming back, so remembered insights have something to save.
RECURRING = {
    "math": ["mul_medium", "chain", "mod"],
    "code": ["factorial", "fizzbuzz", "count_vowels"],
    "qa": ["founder", "anthem"],
}


@dataclass
class E2EConfig:
    seed: int = 0
    train_per_domain: int = 150
    eval_per_domain: int = 60
    rlcr_steps: int = 8
    days: int = 6
    day_per_domain: int = 40
    memory_budget_bytes: int = 64 * 1024
    memory_index: str = "numpy"
    poison_day: int = 3


def make_teacher() -> MockModel:
    # Cost per loop scales with parameter count: a 27B teacher vs a ~1.7B student is ~16x.
    return MockModel(
        "oracle",
        {"math": 0.95, "code": 0.95, "qa": 0.95},
        overconfidence=0.0,
        awareness=0.95,
        cost_per_loop=16.0,
        version="mock-oracle",
    )


def make_student() -> MockModel:
    return MockModel(
        "sprout",
        {"math": 0.45, "code": 0.40, "qa": 0.35},
        overconfidence=0.2,
        awareness=0.1,
        cost_per_loop=1.0,
    )


def run_e2e(config: E2EConfig = E2EConfig(), teacher: ModelBackend | None = None) -> dict:
    """Run every stage. Pass `teacher` to use a real model server instead of the mock."""
    base = config.seed * 1000
    train = make_suite(base + 1, config.train_per_domain)
    holdout = make_suite(base + 2, config.eval_per_domain)
    tune_set, test_set = holdout[::2], holdout[1::2]
    golden = GoldenSet(make_suite(base + 3, config.eval_per_domain))
    teacher = CachedBackend(teacher or make_teacher())
    student = make_student()

    def student_eval() -> dict:
        return evaluate(lambda p: student.answer(p, max_loops=4), test_set)

    report: dict = {"config": asdict(config)}
    report["p0_baseline"] = {
        "teacher": evaluate(lambda p: teacher.answer(p, max_loops=8), test_set),
        "student": student_eval(),
    }
    report["p1_distill"] = {**distill(teacher, student, train), "student": student_eval()}

    pool = learnable_problems(student, train)
    history = run_rlcr(student, pool, steps=config.rlcr_steps, seed=config.seed)
    report["p2_rlcr"] = {"pool": len(pool), "history": history, "student": student_eval()}

    tuned = tune_thresholds(student, teacher, tune_set)
    thresholds = tuned["thresholds"]
    triage = Triage(student, teacher, None, thresholds)
    report["p3_triage"] = {
        "thresholds": asdict(thresholds),
        "met_target_on_tune_set": tuned["met_target"],
        "recommended_policy": tuned["recommended_policy"],
        "pareto": tuned["pareto"],
        "teacher_only": run_policy(lambda p: teacher_only(teacher, p), test_set),
        "triage": run_policy(triage.solve, test_set),
    }

    report["p4_hikmat"] = run_hikmat_days(student, teacher, thresholds, golden, config)
    report["golden_tamper_detected"] = _tamper_is_detected(golden)
    report["teacher_calls"] = {"made": teacher.misses, "served_from_cache": teacher.hits}
    return report


def run_hikmat_days(
    student: MockModel, teacher: ModelBackend, thresholds: Thresholds, golden: GoldenSet, config: E2EConfig
) -> dict:
    memory = HikmatMemory(
        CodonCodec(FEATURE_DIM, student.version),
        budget_bytes=config.memory_budget_bytes,
        index=config.memory_index,
    )
    autopilot = Autopilot(student, memory, golden)
    golden_before = autopilot.baseline["accuracy"]
    triage = Triage(student, teacher, memory, thresholds)
    days, step = [], 0
    for day in range(config.days):
        problems = make_suite(config.seed * 1000 + 100 + day, config.day_per_domain, families=RECURRING)
        attacks = _inject_poison(memory, step) if day == config.poison_day else {}
        proposals: Counter = Counter()
        results = []
        for problem in problems:
            step += 1
            result = triage.solve(problem, step=step)
            correct = judge(problem, result.answer)
            results.append((result, correct))
            if result.hint_id is not None and result.hint_id in memory.records:
                saved = memory.records[result.hint_id].loops_spent - result.answer.loops
                memory.credit(result.hint_id, saved)
            # Escalations and long thinking become memories, so next time they are cheap.
            if result.action in ("think", "escalate") and not result.answer.abstained:
                outcome = memory.propose(
                    problem.features,
                    method_tag(problem.family),
                    verified=correct,
                    confidence=result.answer.confidence,
                    loops_spent=triage.think_loops,
                    verify_level=2 if problem.domain == "qa" else 1,
                    step=step,
                )
                proposals[outcome] += 1
        decisions = autopilot.review(problems, step)
        health = autopilot.check_health(step)
        actions = Counter(r.action for r, _ in results)
        reference = run_policy(lambda p: teacher_only(teacher, p), problems)
        days.append(
            {
                "day": day,
                "accuracy": float(np.mean([c for _, c in results])),
                "mean_cost": float(np.mean([r.cost for r, _ in results])),
                "teacher_only_accuracy": reference["accuracy"],
                "teacher_only_cost": reference["mean_cost"],
                "actions": {a: n / len(results) for a, n in sorted(actions.items())},
                "proposals": dict(proposals),
                "decisions": dict(Counter(d["decision"] for d in decisions)),
                "attacks": attacks,
                "golden_accuracy": health["accuracy"],
                "rolled_back": health["rolled_back"],
                "memory": memory.stats(),
            }
        )
    return {"golden_accuracy_without_memory": golden_before, "days": days, "events": autopilot.events}


def _inject_poison(memory: HikmatMemory, step: int) -> dict:
    """Two attacks: a bad insight sent through quarantine (review should reject it), and
    bad insights forced live as if a verifier bug let them through (health check should
    roll them back)."""
    def plant(target: str, wrong: str) -> int:
        outcome = memory.propose(
            family_center(target), method_tag(wrong),
            verified=True, confidence=0.95, loops_spent=8, verify_level=1, step=step,
        )
        if outcome != "quarantined":
            raise RuntimeError(f"poison record was not stored ({outcome}); attack results would be meaningless")
        return max(memory.records)

    quarantined = plant("math:mul_medium", "math:add_small")
    forced = [plant("code:factorial", "code:add"), plant("qa:founder", "qa:capital")]
    for record_id in forced:
        memory.promote(record_id)
    return {"quarantined_poison": quarantined, "forced_poison": forced}


def _tamper_is_detected(golden: GoldenSet) -> bool:
    copy = GoldenSet(list(golden.problems))
    copy._problems = copy._problems[:-1]
    try:
        _ = copy.problems
    except TamperError:
        return True
    return False
