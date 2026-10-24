import pytest

from mycelium.evals.datasets import make_suite
from mycelium.models.cache import CachedBackend
from mycelium.pipeline import E2EConfig, make_teacher, run_e2e
from mycelium.types import Hint


class Counting:
    def __init__(self, inner):
        self.inner, self.calls = inner, 0
        self.name, self.version, self.cost_per_loop = inner.name, inner.version, inner.cost_per_loop

    def answer(self, problem, **kwargs):
        self.calls += 1
        return self.inner.answer(problem, **kwargs)


def test_cache_asks_each_distinct_request_once():
    backend = Counting(make_teacher())
    cached = CachedBackend(backend)
    problem = make_suite(31, 1)[0]
    first = cached.answer(problem, max_loops=8)
    assert cached.answer(problem, max_loops=8) is first
    cached.answer(problem, max_loops=8, sample=1)
    cached.answer(problem, max_loops=8, hint=Hint("method:x", 0.9, 0))
    assert backend.calls == 3 and (cached.hits, cached.misses) == (1, 3)


def test_pipeline_accepts_an_injected_teacher_and_faiss_index():
    pytest.importorskip("faiss")
    small = E2EConfig(train_per_domain=60, eval_per_domain=30, rlcr_steps=3, days=3, day_per_domain=20,
                      poison_day=1, memory_index="faiss-hnsw")
    report = run_e2e(small, teacher=make_teacher())
    assert report["teacher_calls"]["served_from_cache"] > report["teacher_calls"]["made"]
    assert report["golden_tamper_detected"]
    assert all(d["memory"]["used_bytes"] <= d["memory"]["budget_bytes"] for d in report["p4_hikmat"]["days"])
