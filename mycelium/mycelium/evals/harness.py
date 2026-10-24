"""Run a backend over a suite and report accuracy and honesty metrics."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from mycelium.evals import metrics
from mycelium.evals.judges import judge
from mycelium.types import Answer, Problem

Solver = Callable[[Problem], Answer]


def evaluate(solver: Solver, problems: list[Problem]) -> dict:
    answers = [solver(p) for p in problems]
    correct = np.array([judge(p, a) for p, a in zip(problems, answers, strict=True)])
    confidence = np.array([a.confidence for a in answers])
    abstained = np.array([a.abstained for a in answers])
    answerable = np.array([p.answerable for p in problems])
    return {
        "n": len(problems),
        "accuracy": float(correct.mean()),
        # None when every problem is unanswerable (e.g. the fictional-entity questions alone).
        "accuracy_answerable": float(correct[answerable].mean()) if answerable.any() else None,
        "ece": metrics.expected_calibration_error(confidence, correct),
        "brier": metrics.brier_score(confidence, correct),
        "auroc": metrics.auroc(confidence, correct),
        "hallucination_rate": metrics.hallucination_rate(confidence, correct, abstained),
        "abstain_rate": float(abstained.mean()),
        "mean_loops": float(np.mean([a.loops for a in answers])),
    }
