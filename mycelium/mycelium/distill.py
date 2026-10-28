"""P1: distillation. The teacher answers, JUDGE keeps only verified answers, the student learns."""

from __future__ import annotations

from mycelium.evals.judges import judge
from mycelium.models.base import ModelBackend, TrainableBackend
from mycelium.types import Problem


def build_distillation_set(
    teacher: ModelBackend, problems: list[Problem], *, max_loops: int = 8, attempts: int = 2
) -> list[tuple[Problem, str]]:
    """Rejection sampling: up to `attempts` teacher tries per problem, keep the first verified one."""
    records = []
    for problem in problems:
        if not problem.answerable:
            continue
        for sample in range(attempts):
            answer = teacher.answer(problem, max_loops=max_loops, sample=sample)
            if judge(problem, answer):
                records.append((problem, answer.text))
                break
    return records


def distill(teacher: ModelBackend, student: TrainableBackend, problems: list[Problem]) -> dict:
    records = build_distillation_set(teacher, problems)
    student.learn_sft(records)
    return {"problems": len(problems), "verified_records": len(records)}
