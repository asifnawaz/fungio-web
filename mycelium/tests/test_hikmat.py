import numpy as np
import pytest

from mycelium.evals.datasets import FEATURE_DIM, family_center, make_suite
from mycelium.hikmat.codec import CodonCodec
from mycelium.hikmat.memory import AdmissionPolicy, HikmatMemory


def _vec(seed):
    v = np.random.default_rng(seed).normal(size=FEATURE_DIM)
    return v / np.linalg.norm(v)


def _memory(budget=1 << 20, version="v1"):
    return HikmatMemory(CodonCodec(FEATURE_DIM, version), budget_bytes=budget)


def _propose(memory, key, payload="method:a", **overrides):
    args = dict(verified=True, confidence=0.9, loops_spent=6, verify_level=1, step=0)
    args.update(overrides)
    return memory.propose(key, payload, **args)


def test_codec_is_small_and_faithful():
    codec = CodonCodec(FEATURE_DIM, "v1")
    v = _vec(0)
    codes = codec.encode(v)
    assert len(codes) == codec.nbytes == FEATURE_DIM // 4
    assert float(codec.decode(codes) @ v) > 0.85


def test_codec_versions_are_incompatible():
    v = _vec(1)
    assert CodonCodec(FEATURE_DIM, "v1").encode(v) == CodonCodec(FEATURE_DIM, "v1").encode(v)
    assert CodonCodec(FEATURE_DIM, "v1").encode(v) != CodonCodec(FEATURE_DIM, "v2").encode(v)


def test_codec_rejects_bad_dim():
    with pytest.raises(ValueError):
        CodonCodec(30, "v1")


@pytest.mark.parametrize(
    "overrides,outcome",
    [
        ({"verified": False}, "rejected:unverified"),
        ({"loops_spent": 1}, "rejected:cheap"),
        ({"confidence": 0.5}, "rejected:unsure"),
    ],
)
def test_admission_policy(overrides, outcome):
    assert _propose(_memory(), _vec(2), **overrides) == outcome


def test_quarantined_records_are_not_used_until_promoted():
    memory = _memory()
    key = family_center("math:chain")
    assert _propose(memory, key) == "quarantined"
    assert memory.lookup(key) is None
    (record,) = memory.ready_for_review()
    memory.promote(record.id)
    hint = memory.lookup(key)
    assert hint.text == "method:a" and hint.similarity > 0.85


def test_similar_insights_merge():
    memory = _memory()
    problems = [p for p in make_suite(3, 30) if p.family == "math:mod"][:3]
    outcomes = [_propose(memory, p.features) for p in problems]
    assert outcomes[0] == "quarantined"
    assert "merged" in outcomes[1:]
    assert len(memory.records) < len(problems)


def test_facts_need_independent_support_before_review():
    memory = HikmatMemory(CodonCodec(FEATURE_DIM, "v1"), budget_bytes=1 << 20, policy=AdmissionPolicy())
    key = family_center("qa:founder")
    _propose(memory, key, verify_level=2)
    assert memory.ready_for_review() == []
    _propose(memory, key, verify_level=2)
    assert len(memory.ready_for_review()) == 1


def test_budget_is_never_exceeded():
    memory = _memory(budget=600)
    for i in range(40):
        _propose(memory, _vec(100 + i), payload=f"method:{i}", step=i)
        assert memory.used_bytes <= 600
    assert 0 < len(memory.records) < 40


def test_trial_snapshot_restore_and_expiry():
    memory = _memory()
    key = family_center("code:factorial")
    _propose(memory, key)
    record_id = next(iter(memory.records))
    with memory.trial(record_id):
        assert memory.lookup(key, count=False) is not None
    assert memory.lookup(key) is None

    snapshot = memory.snapshot()
    memory.reject(record_id)
    _propose(memory, family_center("qa:anthem"))
    memory.restore(snapshot)
    assert set(memory.records) == {record_id}
    # Ids never repeat after a rollback, so audit logs stay unambiguous.
    _propose(memory, family_center("math:mod"))
    assert max(memory.records) == record_id + 2

    assert memory.expire_quarantine(step=5000, max_age=1000) == 2
    assert not memory.records


def test_other_model_versions_are_dropped():
    memory = _memory(version="v1")
    _propose(memory, _vec(5))
    memory.codec = CodonCodec(FEATURE_DIM, "v2")
    assert memory.drop_other_versions() == 1
