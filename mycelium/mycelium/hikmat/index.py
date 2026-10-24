"""Vector indexes for HIKMAT lookups.

`NumpyIndex` keeps one contiguous float32 matrix, so a search is a single matrix-vector
product (exact, no extra dependency). `FaissHNSWIndex` uses an HNSW graph from FAISS for
sublinear search at millions of records (approximate; install `faiss-cpu`).
"""

from __future__ import annotations

from typing import Protocol

import numpy as np


class VectorIndex(Protocol):
    def add(self, key: int, vector: np.ndarray) -> None: ...

    def remove(self, key: int) -> None: ...

    def search(self, vector: np.ndarray, k: int) -> list[tuple[int, float]]:
        """Up to k (key, inner product) pairs, best first."""
        ...

    def __len__(self) -> int: ...


class NumpyIndex:
    def __init__(self, dim: int, capacity: int = 1024):
        self.dim = dim
        self._matrix = np.zeros((capacity, dim), dtype=np.float32)
        self._keys: list[int] = []
        self._row: dict[int, int] = {}

    def __len__(self) -> int:
        return len(self._keys)

    def add(self, key: int, vector: np.ndarray) -> None:
        if key in self._row:
            raise KeyError(f"duplicate key {key}")
        if len(self._keys) == len(self._matrix):
            self._matrix = np.concatenate([self._matrix, np.zeros_like(self._matrix)])
        self._row[key] = len(self._keys)
        self._matrix[len(self._keys)] = vector
        self._keys.append(key)

    def remove(self, key: int) -> None:
        row = self._row.pop(key, None)
        if row is None:
            return
        last = len(self._keys) - 1
        if row != last:
            # Swap the last row into the hole so the matrix stays contiguous.
            moved = self._keys[last]
            self._matrix[row] = self._matrix[last]
            self._keys[row] = moved
            self._row[moved] = row
        self._keys.pop()

    def search(self, vector: np.ndarray, k: int) -> list[tuple[int, float]]:
        n = len(self._keys)
        if n == 0:
            return []
        scores = self._matrix[:n] @ np.asarray(vector, dtype=np.float32)
        k = min(k, n)
        top = np.argpartition(-scores, k - 1)[:k]
        top = top[np.argsort(-scores[top])]
        return [(self._keys[i], float(scores[i])) for i in top]


class FaissHNSWIndex:
    """HNSW graph over inner product. HNSW cannot delete, so removals are tombstoned and
    the graph is rebuilt once tombstones pass `rebuild_ratio` of its size."""

    def __init__(self, dim: int, m: int = 32, ef_search: int = 64, rebuild_ratio: float = 0.25):
        import faiss  # optional dependency

        self._faiss = faiss
        self.dim, self.m, self.ef_search, self.rebuild_ratio = dim, m, ef_search, rebuild_ratio
        self._vectors: dict[int, np.ndarray] = {}
        self._dead: set[int] = set()
        self._build([])

    def _build(self, keys: list[int]) -> None:
        index = self._faiss.IndexHNSWFlat(self.dim, self.m, self._faiss.METRIC_INNER_PRODUCT)
        index.hnsw.efSearch = self.ef_search
        self._index = self._faiss.IndexIDMap(index)
        if keys:
            matrix = np.stack([self._vectors[k] for k in keys]).astype(np.float32)
            self._index.add_with_ids(matrix, np.asarray(keys, dtype=np.int64))
        self._dead.clear()

    def __len__(self) -> int:
        return len(self._vectors)

    def add(self, key: int, vector: np.ndarray) -> None:
        if key in self._vectors or key in self._dead:
            raise KeyError(f"duplicate key {key}")
        v = np.asarray(vector, dtype=np.float32)
        self._vectors[key] = v
        self._index.add_with_ids(v[None, :], np.asarray([key], dtype=np.int64))

    def remove(self, key: int) -> None:
        if self._vectors.pop(key, None) is None:
            return
        self._dead.add(key)
        if len(self._dead) > self.rebuild_ratio * max(1, len(self._vectors)):
            self._build(list(self._vectors))

    def search(self, vector: np.ndarray, k: int) -> list[tuple[int, float]]:
        if not self._vectors:
            return []
        fetch = min(k + len(self._dead), self._index.ntotal)
        scores, ids = self._index.search(np.asarray(vector, dtype=np.float32)[None, :], fetch)
        hits = [(int(i), float(s)) for i, s in zip(ids[0], scores[0], strict=True) if i >= 0 and i in self._vectors]
        return hits[:k]


def make_index(kind: str, dim: int) -> VectorIndex:
    if kind == "numpy":
        return NumpyIndex(dim)
    if kind == "faiss-hnsw":
        return FaissHNSWIndex(dim)
    raise ValueError(f"unknown index kind {kind!r}")
