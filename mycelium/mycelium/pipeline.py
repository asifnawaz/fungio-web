"""End-to-end v0.1 pipeline: P0 baseline -> P1 distill -> P2 RLCR -> P3 TRIAGE -> P4 HIKMAT days.

With the mock backend this runs on a CPU in under a minute and checks that every stage
moves its metric in the right direction and that the safety gates fire when attacked.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import asdict, dataclass, field

import numpy as np

from mycelium.autopilot import Autopilot, GoldenSet, TamperError
from mycelium.distill import distill
from mycelium.evals.datasets import FEATURE_DIM, family_center, make_suite, stable_seed
from mycelium.evals.harness import evaluate
from mycelium.evals.judges import judge
from mycelium.evals.real import load_gsm_symbolic, load_mmlu, load_real, split
from mycelium.hikmat.codec import CodonCodec
from mycelium.hikmat.memory import HikmatMemory
from mycelium.models.base import ModelBackend
from mycelium.models.cache import CachedBackend
from mycelium.models.mock import MockModel, method_tag
from mycelium.rlcr import learnable_problems, run_rlcr
from mycelium.router import Thresholds, Triage, run_policy, teacher_only, tune_thresholds
from mycelium.types import Problem

# Harder families that keep coming back, so remembered insights have something to save.
RECURRING = {
    "math": ["mul_medium", "chain", "mod"],
    "code": ["factorial", "fizzbuzz", "count_vowels"],
    "qa": ["founder", "anthem"],
}


@dataclass
class E2EConfig:
    seed: int = 0
    # "synthetic": generated arithmetic, code and fictional-world QA.
    # "real": committed GSM8K + MMLU science/math samples, plus fictional unanswerables.
    # "symbolic": like "real", with GSM-Symbolic variants (shared templates) instead of GSM8K.
    suite: str = "synthetic"
    # "basic": steady traffic. "complex": topic drift across days, a student that is
    # most overconfident where it is weakest, and a teacher with a blind spot.
    scenario: str = "basic"
    train_per_domain: int = 150
    eval_per_domain: int = 60
    rlcr_steps: int = 8
    days: int = 6
    day_per_domain: int = 40
    day_size: int = 120
    memory_budget_bytes: int = 64 * 1024
    memory_index: str = "numpy"
    poison_day: int = 3
    # Assumed effect of a matching hint on the simulated student (the quantity real
    # models must measure) and how much of it carries to other problems of the same
    # family for math and code. None keeps the defaults in `models.mock`.
    hint_gain: float = 0.4
    procedural_transfer: float | None = None


@dataclass
class Suite:
    train: list[Problem]
    tune: list[Problem]
    test: list[Problem]
    golden: list[Problem]
    day_problems: Callable[[int], list[Problem]]
    # (target family, misleading family) pairs for the poison attacks.
    quarantined_poison: tuple[str, str]
    forced_poison: list[tuple[str, str]]
    student_family_skill: dict[str, float] = field(default_factory=dict)
    teacher_family_skill: dict[str, float] = field(default_factory=dict)


def make_teacher(family_skill: dict[str, float] | None = None) -> MockModel:
    # Cost per loop scales with parameter count: a 27B teacher vs a ~1.7B student is ~16x.
    return MockModel(
        "oracle",
        {"math": 0.95, "code": 0.95, "qa": 0.95, "mcq": 0.95},
        overconfidence=0.0,
        awareness=0.95,
        cost_per_loop=16.0,
        version="mock-oracle",
        family_skill=family_skill,
    )


def make_student(
    family_skill: dict[str, float] | None = None,
    dunning_kruger: float = 0.0,
    hint_gain: float = 0.4,
    procedural_transfer: float | None = None,
) -> MockModel:
    transfer = None
    if procedural_transfer is not None:
        transfer = {"math": procedural_transfer, "code": procedural_transfer, "qa": 0.0, "mcq": 0.0}
    return MockModel(
        "sprout",
        {"math": 0.45, "code": 0.40, "qa": 0.35, "mcq": 0.45},
        overconfidence=0.2,
        awareness=0.1,
        cost_per_loop=1.0,
        hint_gain=hint_gain,
        family_skill=family_skill,
        dunning_kruger=dunning_kruger,
        family_transfer=transfer,
    )


def _drifting_sampler(pool: list[Problem], size: int, seed: int, drift: bool) -> Callable[[int], list[Problem]]:
    """Each day draws `size` problems from `pool`. With drift, a rotating group of
    families is four times as likely on a given day, so traffic shifts over time."""
    families = sorted({p.family for p in pool})

    def day_problems(day: int) -> list[Problem]:
        rng = np.random.default_rng(stable_seed("day", seed, day))
        weights = np.ones(len(pool))
        if drift:
            focus = {families[(2 * day + k) % len(families)] for k in range(max(1, len(families) // 4))}
            weights = np.array([4.0 if p.family in focus else 1.0 for p in pool])
        picks = rng.choice(len(pool), size=size, replace=True, p=weights / weights.sum())
        return [pool[i] for i in picks]

    return day_problems


def build_synthetic_suite(config: E2EConfig) -> Suite:
    base = config.seed * 1000
    holdout = make_suite(base + 2, config.eval_per_domain)
    complex_ = config.scenario == "complex"
    if complex_:
        pool = [p for d in range(4) for p in make_suite(base + 100 + d, config.day_per_domain, families=RECURRING)]

        def day_problems(day: int) -> list[Problem]:
            return _drifting_sampler(pool, config.day_size, config.seed, drift=True)(day)
    else:
        def day_problems(day: int) -> list[Problem]:
            return make_suite(base + 100 + day, config.day_per_domain, families=RECURRING)
    return Suite(
        train=make_suite(base + 1, config.train_per_domain),
        tune=holdout[::2],
        test=holdout[1::2],
        golden=make_suite(base + 3, config.eval_per_domain),
        day_problems=day_problems,
        quarantined_poison=("math:mul_medium", "math:add_small"),
        forced_poison=[("code:factorial", "code:add"), ("qa:founder", "qa:capital")],
        student_family_skill={"code:factorial": -0.1, "math:chain": -0.1} if complex_ else {},
        teacher_family_skill={"code:fizzbuzz": -0.3} if complex_ else {},
    )


def _unanswerables(seed: int, count: int) -> list[Problem]:
    """Fictional-entity questions nobody can answer, to keep honesty measurable."""
    found: list[Problem] = []
    offset = 0
    while len(found) < count:
        found += [p for p in make_suite(seed + offset, 100) if not p.answerable]
        offset += 1
    return found[:count]


# GSM-Symbolic slice for `--suite symbolic`: 40 templates x 6 variants = 240 word problems.
SYMBOLIC_TEMPLATES, SYMBOLIC_VARIANTS = 40, 6


def build_real_suite(config: E2EConfig) -> Suite:
    if config.suite == "symbolic":
        # Same reasoning, new names and numbers: a remembered method can transfer honestly.
        real = load_gsm_symbolic(templates=SYMBOLIC_TEMPLATES, per_template=SYMBOLIC_VARIANTS) + load_mmlu()
    else:
        real = load_real()
    train, holdout, golden = split(real, (0.5, 0.3, 0.2), seed=config.seed)
    u_train, u_holdout, u_golden = split(_unanswerables(config.seed * 1000 + 900, 40), (0.5, 0.3, 0.2))
    holdout = holdout + u_holdout
    complex_ = config.scenario == "complex"
    return Suite(
        train=train + u_train,
        tune=holdout[::2],
        test=holdout[1::2],
        golden=golden + u_golden,
        # Deployment traffic comes from the same kinds of questions; the golden set stays unseen.
        day_problems=_drifting_sampler(train + holdout, config.day_size, config.seed, drift=complex_),
        quarantined_poison=("math:gsm8k-medium", "math:gsm8k-short"),
        forced_poison=[("mcq:high_school_physics", "mcq:astronomy"), ("mcq:college_biology", "mcq:high_school_chemistry")],
        # Weak in chemistry and physics, stronger in biology.
        student_family_skill={
            "mcq:high_school_chemistry": -0.15,
            "mcq:high_school_physics": -0.1,
            "mcq:conceptual_physics": -0.05,
            "mcq:high_school_biology": 0.1,
            "mcq:college_biology": 0.05,
        },
        teacher_family_skill={"mcq:high_school_chemistry": -0.35} if complex_ else {},
    )


def run_e2e(config: E2EConfig = E2EConfig(), teacher: ModelBackend | None = None) -> dict:
    """Run every stage. Pass `teacher` to use a real model server instead of the mock."""
    suite = build_real_suite(config) if config.suite in ("real", "symbolic") else build_synthetic_suite(config)
    train, tune_set, test_set = suite.train, suite.tune, suite.test
    golden = GoldenSet(suite.golden)
    teacher = CachedBackend(teacher or make_teacher(suite.teacher_family_skill))
    student = make_student(
        suite.student_family_skill,
        dunning_kruger=0.8 if config.scenario == "complex" else 0.0,
        hint_gain=config.hint_gain,
        procedural_transfer=config.procedural_transfer,
    )

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

    report["suite"] = {
        "name": config.suite,
        "scenario": config.scenario,
        "sizes": {"train": len(train), "tune": len(tune_set), "test": len(test_set), "golden": len(suite.golden)},
        "families": len({p.family for p in train}),
    }
    report["per_family"] = _per_family_accuracy(student, test_set)
    report["p4_hikmat"] = run_hikmat_days(student, teacher, thresholds, golden, config, suite)
    report["golden_tamper_detected"] = _tamper_is_detected(golden)
    report["teacher_calls"] = {"made": teacher.misses, "served_from_cache": teacher.hits}
    return report


def _per_family_accuracy(student: MockModel, problems: list[Problem]) -> dict[str, dict]:
    """Accuracy and mean confidence per family: where the student is weak and whether it knows."""
    rows: dict[str, list[tuple[bool, float]]] = {}
    for p in problems:
        if not p.answerable:
            continue
        a = student.answer(p, max_loops=4)
        rows.setdefault(p.family, []).append((judge(p, a), a.confidence))
    return {
        family: {
            "n": len(r),
            "accuracy": float(np.mean([c for c, _ in r])),
            "mean_confidence": float(np.mean([conf for _, conf in r])),
        }
        for family, r in sorted(rows.items())
    }


def run_hikmat_days(
    student: MockModel,
    teacher: ModelBackend,
    thresholds: Thresholds,
    golden: GoldenSet,
    config: E2EConfig,
    suite: Suite,
) -> dict:
    memory = HikmatMemory(
        CodonCodec(FEATURE_DIM, student.version),
        budget_bytes=config.memory_budget_bytes,
        index=config.memory_index,
    )
    autopilot = Autopilot(student, memory, golden)
    golden_before = autopilot.baseline["accuracy"]
    triage = Triage(student, teacher, memory, thresholds)
    # Same router without memory: the difference to `triage` is what memory itself adds.
    no_memory = Triage(student, teacher, None, thresholds)
    days, step = [], 0
    seen_templates: set[str] = set()
    for day in range(config.days):
        problems = suite.day_problems(day)
        attacks = _inject_poison(memory, step, suite) if day == config.poison_day else {}
        proposals: Counter = Counter()
        retrieval: Counter = Counter()
        repeats = 0
        results = []
        for problem in problems:
            step += 1
            repeats += problem.template_key in seen_templates
            seen_templates.add(problem.template_key)
            result = triage.solve(problem, step=step)
            correct = judge(problem, result.answer)
            results.append((result, correct))
            if result.hint_id is not None and result.hint_id in memory.records:
                record = memory.records[result.hint_id]
                memory.credit(result.hint_id, record.loops_spent - result.answer.loops)
                retrieval[_match_kind(record, problem)] += 1
                retrieval["correct_after_hint"] += correct
            # Escalations and long thinking become memories, so next time they are cheap.
            if result.action in ("think", "escalate") and not result.answer.abstained:
                outcome = memory.propose(
                    problem.features,
                    method_tag(problem.family),
                    verified=correct,
                    confidence=result.answer.confidence,
                    loops_spent=triage.think_loops,
                    # Facts and multiple choice need two confirmations; math and code are machine-checked.
                    verify_level=2 if problem.domain in ("qa", "mcq") else 1,
                    step=step,
                    source=problem.template_key,
                )
                proposals[outcome] += 1
        decisions = autopilot.review(problems, step)
        health = autopilot.check_health(step)
        actions = Counter(r.action for r, _ in results)
        reference = run_policy(lambda p: teacher_only(teacher, p), problems)
        ablation = run_policy(no_memory.solve, problems)
        days.append(
            {
                "day": day,
                "accuracy": float(np.mean([c for _, c in results])),
                "mean_cost": float(np.mean([r.cost for r, _ in results])),
                "teacher_only_accuracy": reference["accuracy"],
                "teacher_only_cost": reference["mean_cost"],
                "no_memory_accuracy": ablation["accuracy"],
                "no_memory_cost": ablation["mean_cost"],
                "actions": {a: n / len(results) for a, n in sorted(actions.items())},
                # Share of today's problems whose template was seen before (today or earlier).
                "repeat_rate": repeats / len(problems),
                # What retrieved hints matched: same template, same family only, or another family.
                "retrieval": dict(retrieval),
                "proposals": dict(proposals),
                "decisions": dict(Counter(d["decision"] for d in decisions)),
                "attacks": attacks,
                "golden_accuracy": health["accuracy"],
                "rolled_back": health["rolled_back"],
                "memory": memory.stats(),
            }
        )
    return {"golden_accuracy_without_memory": golden_before, "days": days, "events": autopilot.events}


def _match_kind(record, problem: Problem) -> str:
    if record.payload != method_tag(problem.family):
        return "other_family"
    if not record.source or record.source == problem.template_key:
        return "same_template"
    return "same_family_only"


def _inject_poison(memory: HikmatMemory, step: int, suite: Suite) -> dict:
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

    quarantined = plant(*suite.quarantined_poison)
    forced = [plant(target, wrong) for target, wrong in suite.forced_poison]
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
