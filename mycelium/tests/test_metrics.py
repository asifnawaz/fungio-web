import math

from mycelium.evals.metrics import auroc, brier_score, expected_calibration_error, hallucination_rate


def test_ece_zero_when_confidence_matches_accuracy():
    confidence = [0.25] * 4 + [0.75] * 4
    correct = [1, 0, 0, 0, 1, 1, 1, 0]
    assert expected_calibration_error(confidence, correct) == 0.0


def test_ece_detects_overconfidence():
    assert math.isclose(expected_calibration_error([0.95] * 4, [1, 0, 1, 0]), 0.45)


def test_brier():
    assert brier_score([1.0, 0.0], [1, 0]) == 0.0
    assert brier_score([1.0, 1.0], [0, 0]) == 1.0


def test_auroc_perfect_random_and_undefined():
    assert auroc([0.9, 0.8, 0.2, 0.1], [1, 1, 0, 0]) == 1.0
    assert auroc([0.5, 0.5], [1, 0]) == 0.5
    assert math.isnan(auroc([0.5, 0.6], [1, 1]))


def test_hallucination_counts_confident_wrong_answers_only():
    rate = hallucination_rate(
        confidence=[0.9, 0.9, 0.3, 0.9],
        correct=[True, False, False, False],
        abstained=[False, False, False, True],
    )
    assert rate == 0.25
