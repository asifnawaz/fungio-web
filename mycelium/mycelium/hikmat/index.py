"""Vector indexes for HIKMAT lookups.

`NumpyIndex` keeps one contiguous float32 matrix, so a search is a single matrix-vector
product (exact, no extra dependency). `FaissHNSWIndex` uses an HNSW graph from FAISS for
sublinear search at millions of records (approximate; install `faiss-cpu`).
`BinaryIndex` (`binary-ivf`) searches exactly while small and, with FAISS installed,
switches to a clustered binary IVF (XOR + popcount shortlist, exact rerank) once large.
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


class BinaryIndex:
    """Exact search while small, XOR-IVF shortlist + exact rerank once large.

    Below `ivf_threshold` vectors (or without FAISS) it searches exactly, which is the
    fastest option at that size. Above it, each vector's sign bits (64 dims -> 8 bytes)
    go into a FAISS binary IVF: only `nprobe` clusters are scanned, Hamming distance
    (popcount of XOR) picks a shortlist, and the shortlist is reranked with exact inner
    products so scores mean the same as in `NumpyIndex`. The IVF is retrained whenever
    the index doubles. A plain XOR scan in NumPy was measured slower than the float
    product, so it is not offered.
    """

    def __init__(self, dim: int, *, shortlist: int = 64, ivf_threshold: int | None = 10_000, nprobe: int = 8):
        if dim % 8:
            raise ValueError("dim must be a multiple of 8")
        self.dim, self.shortlist, self.ivf_threshold, self.nprobe = dim, shortlist, ivf_threshold, nprobe
        self._floats = NumpyIndex(dim)
        self._bits = np.zeros((len(self._floats._matrix), dim // 8), dtype=np.uint8)
        self._ivf = None
        self._ivf_trained_at = 0
        try:
            import faiss
        except ImportError:
            faiss = None
        self._faiss = faiss if ivf_threshold is not None else None

    def __len__(self) -> int:
        return len(self._floats)

    @staticmethod
    def _signs(vector: np.ndarray) -> np.ndarray:
        return np.packbits(np.asarray(vector) > 0)

    def add(self, key: int, vector: np.ndarray) -> None:
        self._floats.add(key, vector)
        row = self._floats._row[key]
        if row >= len(self._bits):
            self._bits = np.concatenate([self._bits, np.zeros_like(self._bits)])
        self._bits[row] = self._signs(vector)
        if self._ivf is not None:
            self._ivf.add_with_ids(self._bits[row : row + 1], np.asarray([key], dtype=np.int64))
        self._maybe_build_ivf()

    def remove(self, key: int) -> None:
        row = self._floats._row.get(key)
        if row is None:
            return
        last = len(self._floats) - 1
        self._floats.remove(key)
        if row != last:
            self._bits[row] = self._bits[last]
        if self._ivf is not None:
            self._ivf.remove_ids(np.asarray([key], dtype=np.int64))

    def _maybe_build_ivf(self) -> None:
        n = len(self._floats)
        if self._faiss is None or n < self.ivf_threshold or n < 2 * self._ivf_trained_at:
            return
        bits = self._bits[:n]
        # ~4*sqrt(n) clusters, but at least ~39 training points per cluster as FAISS advises.
        nlist = int(np.clip(min(4 * np.sqrt(n), n // 39), 16, 65536))
        quantizer = self._faiss.IndexBinaryFlat(self.dim)
        ivf = self._faiss.IndexBinaryIVF(quantizer, self.dim, nlist)
        sample_size = max(100_000, 39 * nlist)
        sample = bits if n <= sample_size else bits[np.random.default_rng(0).choice(n, sample_size, replace=False)]
        ivf.train(sample)
        ivf.nprobe = self.nprobe
        ivf.add_with_ids(bits, np.asarray(self._floats._keys, dtype=np.int64))
        self._ivf, self._quantizer, self._ivf_trained_at = ivf, quantizer, n

    def search(self, vector: np.ndarray, k: int) -> list[tuple[int, float]]:
        if self._ivf is None:
            return self._floats.search(vector, k)
        want = min(len(self._floats), max(self.shortlist, 4 * k))
        _, ids = self._ivf.search(self._signs(vector)[None, :], want)
        rows = np.asarray([self._floats._row[int(i)] for i in ids[0] if i >= 0], dtype=np.int64)
        if len(rows) == 0:
            return []
        scores = self._floats._matrix[rows] @ np.asarray(vector, dtype=np.float32)
        order = np.argsort(-scores)[:k]
        return [(self._floats._keys[rows[i]], float(scores[i])) for i in order]

    @property
    def uses_ivf(self) -> bool:
        return self._ivf is not None


def make_index(kind: str, dim: int) -> VectorIndex:
    if kind == "numpy":
        return NumpyIndex(dim)
    if kind == "faiss-hnsw":
        return FaissHNSWIndex(dim)
    if kind == "binary-ivf":
        return BinaryIndex(dim)
    raise ValueError(f"unknown index kind {kind!r}")
