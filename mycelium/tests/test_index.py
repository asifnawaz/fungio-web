import numpy as np
import pytest

from mycelium.evals.datasets import FEATURE_DIM
from mycelium.hikmat.codec import CodonCodec
from mycelium.hikmat.index import NumpyIndex, make_index
from mycelium.hikmat.memory import AdmissionPolicy, HikmatMemory


def _unit(rng, n, dim=FEATURE_DIM):
    v = rng.normal(size=(n, dim))
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def test_numpy_index_matches_brute_force_after_removals():
    rng = np.random.default_rng(0)
    vectors = _unit(rng, 3000)
    index = NumpyIndex(FEATURE_DIM, capacity=8)  # forces several resizes
    for i, v in enumerate(vectors):
        index.add(i, v)
    removed = set(range(0, 3000, 3))
    for i in removed:
        index.remove(i)
    index.remove(0)  # removing twice is a no-op
    alive = np.array(sorted(set(range(3000)) - removed))
    assert len(index) == len(alive)
    for q in _unit(rng, 20):
        expected = alive[np.argsort(-(vectors[alive] @ q))[:5]]
        assert [k for k, _ in index.search(q, 5)] == list(expected)


def test_numpy_index_rejects_duplicate_keys():
    index = NumpyIndex(4)
    index.add(1, np.ones(4) / 2)
    with pytest.raises(KeyError):
        index.add(1, np.ones(4) / 2)


def test_faiss_hnsw_recall_and_removal():
    pytest.importorskip("faiss")
    rng = np.random.default_rng(1)
    vectors = _unit(rng, 5000)
    index = make_index("faiss-hnsw", FEATURE_DIM)
    for i, v in enumerate(vectors):
        index.add(i, v)
    # Each stored vector should be its own nearest neighbour.
    found = sum(index.search(vectors[i], 1)[0][0] == i for i in range(0, 5000, 50))
    assert found >= 95
    for i in range(2000):  # crosses the rebuild threshold
        index.remove(i)
    assert len(index) == 3000
    hits = index.search(vectors[10], 10)
    assert all(k >= 2000 for k, _ in hits)
    assert index.search(vectors[4000], 1)[0][0] == 4000


@pytest.mark.parametrize("kind", ["numpy", "faiss-hnsw"])
def test_memory_bookkeeping_with_each_index(kind):
    if kind == "faiss-hnsw":
        pytest.importorskip("faiss")
    rng = np.random.default_rng(2)
    memory = HikmatMemory(
        CodonCodec(FEATURE_DIM, "v1"), budget_bytes=4000,
        policy=AdmissionPolicy(merge_similarity=1.1), index=kind,
    )
    keys = _unit(rng, 200)
    for i, key in enumerate(keys):
        memory.propose(key, f"m{i}", verified=True, confidence=0.9, loops_spent=5, verify_level=1, step=i)
        assert memory.used_bytes == sum(r.nbytes for r in memory.records.values()) <= 4000
    survivor = max(memory.records)
    memory.promote(survivor)
    assert memory.lookup(keys[survivor], count=False).record_id == survivor

    snapshot = memory.snapshot()
    for record_id in list(memory.records):
        memory.reject(record_id)
    assert memory.used_bytes == 0 and memory.lookup(keys[survivor]) is None
    memory.restore(snapshot)
    assert memory.used_bytes == sum(r.nbytes for r in memory.records.values())
    assert memory.lookup(keys[survivor], count=False).record_id == survivor
