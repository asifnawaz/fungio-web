"""Benchmark HIKMAT vector indexes on clustered synthetic keys.

    python -m mycelium.cli bench --n 100000

Keys come in families (like real problem types), so "right family" is the recall that
matters for HIKMAT: a hint from the same family is useful even if it is not the single
closest record.
"""

from __future__ import annotations

import time

import numpy as np

from mycelium.hikmat.index import make_index


def clustered_keys(n: int, dim: int, families: int, rng: np.random.Generator):
    centres = rng.normal(size=(families, dim)).astype(np.float32)
    centres /= np.linalg.norm(centres, axis=1, keepdims=True)
    labels = rng.integers(0, families, n)
    keys = centres[labels] + rng.normal(scale=0.3 / np.sqrt(dim), size=(n, dim)).astype(np.float32)
    keys /= np.linalg.norm(keys, axis=1, keepdims=True)
    return keys, labels, centres


def available_kinds() -> list[str]:
    kinds = ["numpy"]
    try:
        import faiss  # noqa: F401
    except ImportError:
        return kinds
    return [*kinds, "binary-ivf", "faiss-hnsw"]


def benchmark(n: int = 100_000, queries: int = 500, dim: int = 64, seed: int = 0, kinds: list[str] | None = None) -> list[dict]:
    rng = np.random.default_rng(seed)
    keys, labels, centres = clustered_keys(n, dim, families=max(10, n // 50), rng=rng)
    query_labels = rng.integers(0, len(centres), queries)
    query_keys = centres[query_labels] + rng.normal(scale=0.3 / np.sqrt(dim), size=(queries, dim)).astype(np.float32)
    query_keys /= np.linalg.norm(query_keys, axis=1, keepdims=True)

    rows = []
    for kind in kinds or available_kinds():
        index = make_index(kind, dim)
        start = time.perf_counter()
        for key, vector in enumerate(keys):
            index.add(key, vector)
        build_s = time.perf_counter() - start
        start = time.perf_counter()
        found = [index.search(q, 1)[0][0] for q in query_keys]
        search_ms = (time.perf_counter() - start) / queries * 1e3
        rows.append(
            {
                "index": kind,
                "build_s": build_s,
                "search_ms": search_ms,
                "right_family": float(np.mean(labels[found] == query_labels)),
            }
        )
    return rows


def format_rows(rows: list[dict], n: int) -> str:
    lines = [f"{n} keys", "index        build      search/query   right family"]
    for r in rows:
        lines.append(f"{r['index']:<12} {r['build_s']:6.1f} s   {r['search_ms']:8.3f} ms    {100 * r['right_family']:5.1f}%")
    return "\n".join(lines)
