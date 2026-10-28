"""RSI must only ever promote a model that is better on the exam, stop when it stops
improving or starts gaming its own problems, and never touch the exam."""

import dataclasses

import pytest

from mycelium.autopilot import GoldenSet, TamperError
from mycelium.distill import build_distillation_set
from mycelium.evals.datasets import make_suite
from mycelium.pipeline import make_student, make_teacher
from mycelium.rsi import RECIPES, RSIConfig, RSILoop, _Bandit, run_rsi


@pytest.fixture(scope="module")
def normal():
    return run_rsi(RSIConfig(generations=6))


def test_promotes_only_on_a_real_exam_gain(normal):
    assert any(g["promoted"] for g in normal["generations"])
    for g in normal["generations"]:
        if g["promoted"]:
            assert g["exam_gain_lower95"] > 0
            assert g["hallucination"][1] <= g["hallucination"][0] + 0.01
    assert normal["end"]["accuracy"] > normal["start"]["accuracy"]


def test_version_changes_with_every_promotion(normal):
    versions = [g["version"] for g in normal["generations"]]
    promotions = sum(g["promoted"] for g in normal["generations"])
    assert versions[-1].count("+rsi") == promotions  # HIKMAT drops insights of older versions


def test_training_on_wrong_traces_is_never_promoted():
    report = run_rsi(RSIConfig(verify="inverted", generations=5, patience=3))
    assert not any(g["promoted"] for g in report["generations"])
    assert report["stop"] == "plateau"
    assert report["end"]["accuracy"] == report["start"]["accuracy"]


def test_a_broken_verifier_cannot_make_the_model_worse():
    report = run_rsi(RSIConfig(verify="off", generations=5))
    assert all(g["exam_gain_lower95"] > 0 for g in report["generations"] if g["promoted"])
    assert report["end"]["accuracy"] >= report["start"]["accuracy"]


def _loop(exam_domain: str, propose_families: dict, config: RSIConfig, propose_domain: str | None = None) -> RSILoop:
    teacher, student = make_teacher(), make_student()
    train = make_suite(1, 60)
    anchor = [r for r in build_distillation_set(teacher, train) if r[0].domain == exam_domain]
    student.learn_sft(anchor)
    exam = [p for p in make_suite(2, 60) if p.domain == exam_domain]
    return RSILoop(
        student, GoldenSet(exam[:30]), exam[30:], anchor,
        lambda seed, n: [
            p for p in make_suite(20_000 + seed, n // 2, families=propose_families)
            if propose_domain is None or p.domain == propose_domain
        ],
        config,
    )


def test_goodhart_stop_when_self_made_problems_improve_but_the_exam_does_not():
    # The exam is code only; the proposer makes only math, so self-gains can't show up on the exam.
    loop = _loop("code", {"math": ["mod"]}, RSIConfig(generations=6, anchor=0, patience=10), propose_domain="math")
    report = loop.run()
    assert report["stop"] == "goodhart"
    assert not any(g["promoted"] for g in report["generations"])


def test_exam_overlap_and_tampering_are_refused():
    loop = _loop("math", {}, RSIConfig(generations=1))
    exam_problem = loop.heldout[0]
    loop.propose = lambda seed, n: [exam_problem]
    with pytest.raises(ValueError):
        loop.run()
    loop = _loop("math", {}, RSIConfig(generations=1))
    first = loop.golden._problems[0]
    loop.golden._problems = (dataclasses.replace(first, answer="0"), *loop.golden._problems[1:])
    with pytest.raises(TamperError):
        loop.run()


def test_bandit_tries_every_recipe_then_prefers_the_best():
    bandit = _Bandit(RECIPES)
    seen = []
    for _ in RECIPES:
        recipe = bandit.choose()
        seen.append(recipe.name)
        bandit.update(recipe, 0.05 if recipe.name == "frontier" else 0.0)
    assert sorted(seen) == sorted(r.name for r in RECIPES)
    assert bandit.choose().name == "frontier"
