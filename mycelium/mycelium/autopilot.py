"""Autopilot: self-improvement without a human in the loop.

Every new insight goes quarantine -> shadow test -> promote or reject. After each round
the golden set is re-run; if accuracy drops or hallucinations rise beyond the limits,
memory rolls back to the last good snapshot. The golden set is fingerprinted, so any
change to it is detected instead of silently making the exam easier.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from mycelium.evals.harness import evaluate
from mycelium.hikmat.memory import HikmatMemory
from mycelium.models.base import ModelBackend
from mycelium.types import Answer, Problem


class TamperError(RuntimeError):
    pass


class GoldenSet:
    def __init__(self, problems: list[Problem]):
        self._problems = tuple(problems)
        self._fingerprint = self._digest()

    def _digest(self) -> str:
        h = hashlib.sha256()
        for p in self._problems:
            h.update(f"{p.id}|{p.domain}|{p.answer}|{p.difficulty}|{p.family}\n".encode())
        return h.hexdigest()

    @property
    def problems(self) -> tuple[Problem, ...]:
        if self._digest() != self._fingerprint:
            raise TamperError("golden set changed since it was frozen")
        return self._problems


@dataclass(frozen=True)
class HealthLimits:
    max_accuracy_drop: float = 0.01
    max_hallucination_rise: float = 0.01


class Autopilot:
    def __init__(
        self,
        student: ModelBackend,
        memory: HikmatMemory,
        golden: GoldenSet,
        *,
        limits: HealthLimits = HealthLimits(),
        max_loops: int = 4,
        quarantine_max_age: int = 1000,
    ):
        self.student = student
        self.memory = memory
        self.golden = golden
        self.limits = limits
        self.max_loops = max_loops
        self.quarantine_max_age = quarantine_max_age
        self.events: list[dict] = []
        self._good_snapshot = memory.snapshot()
        self.baseline = self.health()

    def _solve(self, problem: Problem) -> Answer:
        hint = self.memory.lookup(problem.features, count=False)
        return self.student.answer(problem, max_loops=self.max_loops, hint=hint)

    def health(self) -> dict:
        return evaluate(self._solve, list(self.golden.problems))

    def review(self, recent: list[Problem], step: int) -> list[dict]:
        """Shadow-test each quarantined insight on recent problems it would affect."""
        expired = self.memory.expire_quarantine(step, self.quarantine_max_age)
        if expired:
            self.events.append({"step": step, "type": "expired", "count": expired})
        decisions = []
        for record in self.memory.ready_for_review():
            vector = self.memory.vector(record.id)
            affected = [p for p in recent if float(p.features @ vector) >= self.memory.lookup_similarity]
            if not affected:
                decisions.append({"record": record.id, "decision": "waiting"})
                continue
            before = evaluate(self._solve, affected)
            with self.memory.trial(record.id):
                after = evaluate(self._solve, affected)
            better = (
                after["accuracy"] >= before["accuracy"]
                and after["hallucination_rate"] <= before["hallucination_rate"]
                and after["mean_loops"] <= before["mean_loops"]
            )
            if better:
                self.memory.promote(record.id)
            else:
                self.memory.reject(record.id)
            decision = {
                "record": record.id,
                "decision": "promoted" if better else "rejected",
                "affected": len(affected),
                "accuracy": (before["accuracy"], after["accuracy"]),
                "mean_loops": (before["mean_loops"], after["mean_loops"]),
            }
            decisions.append(decision)
            self.events.append({"step": step, "type": "review", **decision})
        return decisions

    def check_health(self, step: int) -> dict:
        current = self.health()
        degraded = (
            current["accuracy"] < self.baseline["accuracy"] - self.limits.max_accuracy_drop
            or current["hallucination_rate"] > self.baseline["hallucination_rate"] + self.limits.max_hallucination_rise
        )
        if degraded:
            self.memory.restore(self._good_snapshot)
            restored = self.health()
            self.events.append(
                {
                    "step": step,
                    "type": "rollback",
                    "accuracy": (current["accuracy"], restored["accuracy"]),
                    "hallucination_rate": (current["hallucination_rate"], restored["hallucination_rate"]),
                }
            )
            return {**restored, "rolled_back": True}
        self._good_snapshot = self.memory.snapshot()
        # Ratchet: the bar only moves up, so slow drift cannot creep past the limits.
        self.baseline = {
            **current,
            "accuracy": max(self.baseline["accuracy"], current["accuracy"]),
            "hallucination_rate": min(self.baseline["hallucination_rate"], current["hallucination_rate"]),
        }
        return {**current, "rolled_back": False}
