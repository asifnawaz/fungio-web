import pytest

from mycelium.autopilot import Autopilot, GoldenSet, TamperError
from mycelium.distill import distill
from mycelium.evals.datasets import FEATURE_DIM, family_center, make_suite
from mycelium.hikmat.codec import CodonCodec
from mycelium.hikmat.memory import HikmatMemory
from mycelium.models.mock import method_tag
from mycelium.pipeline import make_student, make_teacher


@pytest.fixture(scope="module")
def student():
    model = make_student()
    distill(make_teacher(), model, make_suite(21, 60))
    return model


def _setup(student):
    memory = HikmatMemory(CodonCodec(FEATURE_DIM, student.version), budget_bytes=1 << 20)
    golden = GoldenSet(make_suite(22, 40))
    return memory, Autopilot(student, memory, golden)


def _plant(memory, target, payload):
    memory.propose(family_center(target), method_tag(payload),
                   verified=True, confidence=0.95, loops_spent=8, verify_level=1, step=0)
    return max(memory.records)


def test_golden_set_detects_tampering():
    golden = GoldenSet(make_suite(23, 5))
    assert len(golden.problems) == 15
    golden._problems = golden._problems[1:]
    with pytest.raises(TamperError):
        _ = golden.problems


def test_review_promotes_good_and_rejects_poison(student):
    memory, autopilot = _setup(student)
    good = _plant(memory, "math:chain", "math:chain")
    poison = _plant(memory, "math:mul_medium", "math:add_small")
    recent = make_suite(24, 60, families={"math": ["chain", "mul_medium"]})
    decisions = {d["record"]: d["decision"] for d in autopilot.review(recent, step=1)}
    assert decisions[good] == "promoted"
    assert decisions[poison] == "rejected"
    assert poison not in memory.records


def test_health_check_rolls_back_forced_poison(student):
    memory, autopilot = _setup(student)
    for target, wrong in [("code:factorial", "code:add"), ("qa:founder", "qa:capital"), ("math:chain", "math:mod")]:
        memory.promote(_plant(memory, target, wrong))
    health = autopilot.check_health(step=1)
    assert health["rolled_back"]
    assert not memory.records
    assert autopilot.events[-1]["type"] == "rollback"
