"""Accuracy and honesty metrics: ECE, Brier, AUROC, hallucination and abstain rates."""

from __future__ import annotations

import numpy as np


def expected_calibration_error(confidence, correct, n_bins: int = 10) -> float:
    confidence = np.asarray(confidence, dtype=float)
    correct = np.asarray(correct, dtype=float)
    bins = np.minimum((confidence * n_bins).astype(int), n_bins - 1)
    error = 0.0
    for b in range(n_bins):
        in_bin = bins == b
        if in_bin.any():
            error += in_bin.mean() * abs(confidence[in_bin].mean() - correct[in_bin].mean())
    return float(error)


def brier_score(confidence, correct) -> float:
    confidence = np.asarray(confidence, dtype=float)
    correct = np.asarray(correct, dtype=float)
    return float(np.mean((confidence - correct) ** 2))


def auroc(confidence, correct) -> float:
    """Probability that a random correct answer has higher confidence than a random wrong one."""
    confidence = np.asarray(confidence, dtype=float)
    correct = np.asarray(correct, dtype=bool)
    pos, neg = confidence[correct], confidence[~correct]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    # Mann-Whitney U with ties counted as half.
    greater = (pos[:, None] > neg[None, :]).sum()
    ties = (pos[:, None] == neg[None, :]).sum()
    return float((greater + 0.5 * ties) / (len(pos) * len(neg)))


def hallucination_rate(confidence, correct, abstained, threshold: float = 0.5) -> float:
    """Share of answers that were wrong, not abstained, and stated with confidence >= threshold."""
    confidence = np.asarray(confidence, dtype=float)
    correct = np.asarray(correct, dtype=bool)
    abstained = np.asarray(abstained, dtype=bool)
    return float(np.mean(~correct & ~abstained & (confidence >= threshold)))
