"""Full pipeline on the mock backend: every stage must move its metric the right way and
every safety gate must fire when attacked."""

import numpy as np
import pytest

from mycelium.pipeline import E2EConfig, run_e2e


@pytest.fixture(scope="module")
def report():
    return run_e2e(E2EConfig())


def test_distillation_improves_accuracy(report):
    assert report["p1_distill"]["student"]["accuracy"] > report["p0_baseline"]["student"]["accuracy"]
    assert report["p1_distill"]["verified_records"] > 0


def test_rlcr_improves_honesty(report):
    before, after = report["p1_distill"]["student"], report["p2_rlcr"]["student"]
    assert after["ece"] < before["ece"]
    assert after["hallucination_rate"] <= before["hallucination_rate"]
    assert after["accuracy"] >= before["accuracy"] - 0.02


def test_triage_stays_as_honest_as_the_teacher(report):
    p3 = report["p3_triage"]
    assert p3["triage"]["hallucination_rate"] <= p3["teacher_only"]["hallucination_rate"] + 0.05
    assert p3["triage"]["accuracy"] >= 0.85 * p3["teacher_only"]["accuracy"]
    assert p3["pareto"]


def test_hikmat_makes_later_days_cheaper(report):
    days = report["p4_hikmat"]["days"]
    later = days[1:]
    assert np.mean([d["mean_cost"] for d in later]) < np.mean([d["teacher_only_cost"] for d in later])
    assert np.mean([d["mean_cost"] for d in later]) < days[0]["mean_cost"]
    assert days[-1]["actions"].get("escalate", 0) < days[0]["actions"].get("escalate", 0)
    assert all(d["memory"]["used_bytes"] <= d["memory"]["budget_bytes"] for d in days)


def test_memory_helps_golden_accuracy(report):
    hikmat = report["p4_hikmat"]
    assert hikmat["days"][-1]["golden_accuracy"] > hikmat["golden_accuracy_without_memory"]


def test_safety_gates_fire(report):
    hikmat = report["p4_hikmat"]
    poison_day = hikmat["days"][report["config"]["poison_day"]]
    quarantined = poison_day["attacks"]["quarantined_poison"]
    reviews = {e["record"]: e["decision"] for e in hikmat["events"] if e["type"] == "review"}
    assert reviews[quarantined] == "rejected"
    assert poison_day["rolled_back"]
    assert report["golden_tamper_detected"]
