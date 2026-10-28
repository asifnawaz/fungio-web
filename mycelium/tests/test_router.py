import numpy as np

from mycelium.evals.datasets import FEATURE_DIM, family_center
from mycelium.hikmat.codec import CodonCodec
from mycelium.hikmat.memory import HikmatMemory
from mycelium.router import Thresholds, Triage, pareto_front
from mycelium.types import Answer, Problem


class Scripted:
    """Backend that answers with a fixed confidence, higher when given a hint."""

    def __init__(self, confidence, hinted_confidence=None, cost_per_loop=1.0):
        self.name, self.version, self.cost_per_loop = "scripted", "v1", cost_per_loop
        self.confidence = confidence
        self.hinted_confidence = hinted_confidence
        self.calls = []

    def answer(self, problem, *, max_loops, hint=None, sample=0, stop_at=None):
        self.calls.append(hint)
        confidence = self.hinted_confidence if hint is not None and self.hinted_confidence else self.confidence
        return Answer(problem.answer or "guess", confidence, loops=2)


def _problem(answer="7"):
    return Problem("p1", "math", "q", answer, 0.5, "math:chain", family_center("math:chain"))


def test_confident_student_answers_alone():
    student, teacher = Scripted(0.95), Scripted(0.99, cost_per_loop=16)
    result = Triage(student, teacher).solve(_problem())
    assert result.action == "emit" and not teacher.calls


def test_memory_lookup_happens_first():
    memory = HikmatMemory(CodonCodec(FEATURE_DIM, "v1"), budget_bytes=1 << 20)
    memory.propose(family_center("math:chain"), "method:math:chain",
                   verified=True, confidence=0.9, loops_spent=6, verify_level=1, step=0)
    memory.promote(next(iter(memory.records)))
    student = Scripted(0.3, hinted_confidence=0.95)
    result = Triage(student, Scripted(0.99), memory).solve(_problem())
    assert result.action == "retrieve" and result.hint_id is not None
    assert len(student.calls) == 1 and student.calls[0] is not None


def test_unsure_student_escalates_and_unsure_teacher_abstains():
    thresholds = Thresholds(emit=0.8, think=1.01, abstain=0.5)
    escalated = Triage(Scripted(0.3), Scripted(0.9, cost_per_loop=16), thresholds=thresholds).solve(_problem())
    assert escalated.action == "escalate" and escalated.cost == 2 + 2 * 16

    abstained = Triage(Scripted(0.3), Scripted(0.2), thresholds=thresholds).solve(_problem(None))
    assert abstained.action == "abstain" and abstained.answer.abstained


def test_pareto_front_drops_dominated_points():
    curve = [
        {"thresholds": {"emit": 0.6}, "accuracy": 0.8, "hallucination_rate": 0.2, "mean_cost": 10},
        {"thresholds": {"emit": 0.7}, "accuracy": 0.7, "hallucination_rate": 0.3, "mean_cost": 12},
        {"thresholds": {"emit": 0.9}, "accuracy": 0.9, "hallucination_rate": 0.05, "mean_cost": 20},
    ]
    front = pareto_front(curve)
    assert [c["thresholds"]["emit"] for c in front] == [0.6, 0.9]
    assert np.all(np.diff([c["mean_cost"] for c in front]) >= 0)
