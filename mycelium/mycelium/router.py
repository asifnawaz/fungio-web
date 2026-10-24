"""P3: TRIAGE, the confidence router.

The student answers first. Depending on its calibrated confidence it either answers,
looks for a HIKMAT hint, thinks longer (more loops, several attempts, confidence-weighted
vote), or escalates to the teacher. If the teacher is unsure too, the system abstains.
"""

from __future__ import annotations

import itertools
from collections import defaultdict
from dataclasses import asdict, dataclass

import numpy as np

from mycelium.evals.judges import judge
from mycelium.hikmat.memory import HikmatMemory
from mycelium.models.base import ModelBackend
from mycelium.types import Answer, Hint, Problem

LOOKUP_COST = 0.1


@dataclass(frozen=True)
class Thresholds:
    emit: float = 0.8
    think: float = 0.4
    abstain: float = 0.5


@dataclass
class TriageResult:
    answer: Answer
    action: str
    cost: float
    hint_id: int | None = None


def abstain_from(answer: Answer) -> Answer:
    # Confidence of an abstention = confidence that answering would have been wrong.
    return Answer(text="", confidence=1 - answer.confidence, loops=answer.loops, abstained=True)


class Triage:
    def __init__(
        self,
        student: ModelBackend,
        teacher: ModelBackend | None = None,
        memory: HikmatMemory | None = None,
        thresholds: Thresholds = Thresholds(),
        *,
        base_loops: int = 4,
        think_loops: int = 8,
        think_samples: int = 4,
    ):
        self.student = student
        self.teacher = teacher
        self.memory = memory
        self.thresholds = thresholds
        self.base_loops = base_loops
        self.think_loops = think_loops
        self.think_samples = think_samples

    def solve(self, problem: Problem, *, step: int = 0) -> TriageResult:
        t = self.thresholds
        # Lookup first: it is far cheaper than a reasoning loop, and a good hint lets the
        # student stop early instead of paying for an unhinted attempt.
        cost, hint = 0.0, None
        if self.memory is not None:
            cost += LOOKUP_COST
            hint = self.memory.lookup(problem.features, step=step)
        first = self.student.answer(problem, max_loops=self.base_loops, hint=hint, stop_at=t.emit)
        cost += first.loops * self.student.cost_per_loop
        if first.confidence >= t.emit:
            if hint is not None:
                return TriageResult(first, "retrieve", cost, hint.record_id)
            return TriageResult(first, "emit", cost)

        if first.confidence >= t.think:
            voted, spent = self._think(problem, hint)
            cost += spent
            if voted.confidence >= t.emit:
                return TriageResult(voted, "think", cost)

        if self.teacher is not None:
            expert = self.teacher.answer(problem, max_loops=self.think_loops)
            cost += expert.loops * self.teacher.cost_per_loop
            if expert.confidence < t.abstain:
                return TriageResult(abstain_from(expert), "abstain", cost)
            return TriageResult(expert, "escalate", cost)

        if first.confidence < t.abstain:
            return TriageResult(abstain_from(first), "abstain", cost)
        return TriageResult(first, "emit_low", cost)

    def _think(self, problem: Problem, hint: Hint | None) -> tuple[Answer, float]:
        attempts = [
            self.student.answer(
                problem, max_loops=self.think_loops, hint=hint, sample=s + 1, stop_at=self.thresholds.emit
            )
            for s in range(self.think_samples)
        ]
        weight: dict[str, float] = defaultdict(float)
        for a in attempts:
            weight[a.text] += a.confidence
        best = max(weight, key=weight.get)
        supporters = [a for a in attempts if a.text == best]
        share = len(supporters) / len(attempts)
        confidence = float(np.mean([a.confidence for a in supporters]) * share)
        spent = sum(a.loops for a in attempts) * self.student.cost_per_loop
        return Answer(best, confidence, max(a.loops for a in attempts)), spent


def teacher_only(teacher: ModelBackend, problem: Problem, thresholds: Thresholds = Thresholds(), max_loops: int = 8) -> TriageResult:
    answer = teacher.answer(problem, max_loops=max_loops)
    cost = answer.loops * teacher.cost_per_loop
    if answer.confidence < thresholds.abstain:
        return TriageResult(abstain_from(answer), "abstain", cost)
    return TriageResult(answer, "escalate", cost)


def run_policy(solve, problems: list[Problem]) -> dict:
    results = [solve(p) for p in problems]
    correct = np.array([judge(p, r.answer) for p, r in zip(problems, results, strict=True)])
    actions = [r.action for r in results]
    hallucinated = [
        (not c) and (not r.answer.abstained) and r.answer.confidence >= 0.5 for c, r in zip(correct, results, strict=True)
    ]
    return {
        "accuracy": float(correct.mean()),
        "mean_cost": float(np.mean([r.cost for r in results])),
        "hallucination_rate": float(np.mean(hallucinated)),
        "actions": {a: actions.count(a) / len(actions) for a in sorted(set(actions))},
    }


def tune_thresholds(
    student: ModelBackend,
    teacher: ModelBackend,
    problems: list[Problem],
    *,
    target_ratio: float = 0.9,
    hallucination_margin: float = 0.03,
    memory: HikmatMemory | None = None,
) -> dict:
    """Cheapest thresholds that reach `target_ratio` of the teacher's accuracy without
    hallucinating more than `hallucination_margin` above the teacher."""
    reference = run_policy(lambda p: teacher_only(teacher, p), problems)
    target = target_ratio * reference["accuracy"]
    max_hallucination = reference["hallucination_rate"] + hallucination_margin
    curve = []
    # think > 1 means "never think": self-consistency is the most expensive step and may not pay off.
    think_options = [*np.arange(0.2, 0.8, 0.1), 1.01]
    for emit, think, abstain in itertools.product(np.arange(0.6, 0.96, 0.05), think_options, (0.4, 0.5, 0.6)):
        if emit <= think <= 1:
            continue
        thresholds = Thresholds(round(float(emit), 2), round(float(think), 2), abstain)
        triage = Triage(student, teacher, memory, thresholds)
        result = run_policy(triage.solve, problems)
        curve.append({"thresholds": asdict(thresholds), **result})
    feasible = [c for c in curve if c["accuracy"] >= target and c["hallucination_rate"] <= max_hallucination]
    best = min(feasible, key=lambda c: c["mean_cost"]) if feasible else max(curve, key=lambda c: c["accuracy"])
    cheaper = bool(feasible) and best["mean_cost"] < reference["mean_cost"]
    return {
        "teacher": reference,
        "target_accuracy": target,
        "max_hallucination": max_hallucination,
        "met_target": bool(feasible),
        "best": best,
        "thresholds": Thresholds(**best["thresholds"]),
        # If routing cannot beat the teacher alone at the same honesty, say so.
        "recommended_policy": "triage" if cheaper else "teacher_only",
        "pareto": pareto_front(curve),
    }


def pareto_front(curve: list[dict]) -> list[dict]:
    """Configurations no other configuration beats on cost, accuracy and hallucination at once."""
    def dominates(a: dict, b: dict) -> bool:
        no_worse = (
            a["mean_cost"] <= b["mean_cost"]
            and a["accuracy"] >= b["accuracy"]
            and a["hallucination_rate"] <= b["hallucination_rate"]
        )
        better = (
            a["mean_cost"] < b["mean_cost"]
            or a["accuracy"] > b["accuracy"]
            or a["hallucination_rate"] < b["hallucination_rate"]
        )
        return no_worse and better

    front = [c for c in curve if not any(dominates(o, c) for o in curve)]
    unique = {(c["mean_cost"], c["accuracy"], c["hallucination_rate"]): c for c in front}
    return sorted(
        (
            {k: c[k] for k in ("thresholds", "accuracy", "hallucination_rate", "mean_cost")}
            for c in unique.values()
        ),
        key=lambda c: c["mean_cost"],
    )
