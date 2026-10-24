"""Memory must earn its place: no benefit means no promotions and no savings, and the
reported retrieval stats must say what the hints actually matched."""

import numpy as np
import pytest

from mycelium.evals.datasets import FEATURE_DIM, make_suite
from mycelium.hikmat.codec import CodonCodec
from mycelium.hikmat.memory import HikmatMemory
from mycelium.insights import summarize
from mycelium.models.mock import method_tag
from mycelium.pipeline import E2EConfig, make_student, run_e2e
from mycelium.types import Hint


def test_hint_helps_fully_only_on_its_own_template():
    student = make_student(hint_gain=0.4, procedural_transfer=0.25)
    problem = next(p for p in make_suite(0, 20) if p.domain == "math")
    tag = method_tag(problem.family)
    assert student.hint_shift(problem, Hint(tag, 0.9, 0, source=problem.template_key)) == pytest.approx(0.4)
    assert student.hint_shift(problem, Hint(tag, 0.9, 0, source="math:other-template")) == pytest.approx(0.1)
    fact = next(p for p in make_suite(0, 20) if p.domain == "qa")
    # One fact says nothing about another question of the same subject.
    assert student.hint_shift(fact, Hint(method_tag(fact.family), 0.9, 0, source="another-question")) == 0.0


@pytest.mark.parametrize("gain", [0.4, 0.0, -0.2])
def test_wrong_family_hints_hurt_whatever_the_assumed_gain(gain):
    # Regression: with a negative gain, gain x (-1.5) once turned poison into help.
    student = make_student(hint_gain=gain)
    problem = next(p for p in make_suite(0, 20) if p.domain == "math")
    assert student.hint_shift(problem, Hint("method:qa:capital", 0.9, 0, source=problem.template_key)) < 0


def test_insights_from_different_sources_do_not_merge():
    memory = HikmatMemory(CodonCodec(FEATURE_DIM, "v1"), budget_bytes=1 << 20)
    key = np.ones(FEATURE_DIM) / np.sqrt(FEATURE_DIM)
    args = dict(verified=True, confidence=0.9, loops_spent=6, verify_level=2, step=0)
    assert memory.propose(key, "method:qa:x", source="q1", **args) == "quarantined"
    assert memory.propose(key, "method:qa:x", source="q2", **args) == "quarantined"
    assert memory.propose(key, "method:qa:x", source="q1", **args) == "merged"
    assert memory.lookup(key) is None  # nothing is active before the autopilot promotes it


@pytest.mark.parametrize("gain", [0.0, -0.2])
def test_useless_or_harmful_memory_is_never_promoted(gain):
    # All six days, so the poison day (3) is included: that is where the bug above showed.
    summary = summarize(run_e2e(E2EConfig(hint_gain=gain)))
    assert summary["promoted"] == 0
    assert summary["memory_cost_saving"] <= 0.5
    assert summary["memory_accuracy_gain"] >= -0.01


def test_retrieval_stats_report_what_hints_matched():
    report = run_e2e(E2EConfig(days=3))
    summary = summarize(report)
    assert summary["hints"] > 0
    assert summary["memory_cost_saving"] > 0
    # Synthetic math and code share one template per family, so every useful hint is same-template.
    assert summary["same_template_share"] == 1.0
    for day in report["p4_hikmat"]["days"]:
        assert 0.0 <= day["repeat_rate"] <= 1.0
        assert {"no_memory_accuracy", "no_memory_cost"} <= set(day)
