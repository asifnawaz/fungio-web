"""HIKMAT memory: verified insights from hard problems, looked up by meaning.

Records enter in quarantine and only become usable after the autopilot promotes them.
The store has a hard byte budget; when it is full the least valuable records go first.
Search here is brute force over decoded vectors, which is fine for tests; production
should use an ANN index (HNSW or IVF-PQ) over the same codes.
"""

from __future__ import annotations

import copy
from contextlib import contextmanager
from dataclasses import dataclass, field

import numpy as np

from mycelium.hikmat.codec import CodonCodec
from mycelium.types import Hint

RECORD_OVERHEAD_BYTES = 32


@dataclass
class MemoryRecord:
    id: int
    codes: bytes
    payload: str
    # 1 = machine-checked (math, code), 2 = checked against sources (facts).
    verify_level: int
    confidence: float
    loops_spent: int
    created_step: int
    model_version: str
    status: str = "quarantine"
    support: int = 1
    hits: int = 0
    loops_saved: float = 0.0

    @property
    def nbytes(self) -> int:
        return len(self.codes) + len(self.payload.encode()) + RECORD_OVERHEAD_BYTES


@dataclass
class AdmissionPolicy:
    min_loops: int = 3
    min_confidence: float = 0.8
    merge_similarity: float = 0.85
    # Facts need independent confirmations before review; machine-checked results do not.
    min_support: dict[int, int] = field(default_factory=lambda: {1: 1, 2: 2})


class HikmatMemory:
    def __init__(
        self,
        codec: CodonCodec,
        *,
        budget_bytes: int,
        policy: AdmissionPolicy | None = None,
        lookup_similarity: float = 0.75,
    ):
        self.codec = codec
        self.budget_bytes = budget_bytes
        self.policy = policy or AdmissionPolicy()
        self.lookup_similarity = lookup_similarity
        self.records: dict[int, MemoryRecord] = {}
        self._vectors: dict[int, np.ndarray] = {}
        self._next_id = 0

    @property
    def model_version(self) -> str:
        return self.codec.version

    @property
    def used_bytes(self) -> int:
        return sum(r.nbytes for r in self.records.values())

    # ---- writing ------------------------------------------------------------

    def propose(
        self,
        key: np.ndarray,
        payload: str,
        *,
        verified: bool,
        confidence: float,
        loops_spent: int,
        verify_level: int,
        step: int,
    ) -> str:
        if not verified:
            return "rejected:unverified"
        if loops_spent < self.policy.min_loops:
            return "rejected:cheap"
        if confidence < self.policy.min_confidence:
            return "rejected:unsure"
        codes = self.codec.encode(key)
        vector = self.codec.decode(codes)
        match = self._nearest(vector, statuses=("active", "quarantine"), payload=payload)
        if match and match[1] >= self.policy.merge_similarity:
            match[0].support += 1
            return "merged"
        record = MemoryRecord(
            id=self._next_id,
            codes=codes,
            payload=payload,
            verify_level=verify_level,
            confidence=confidence,
            loops_spent=loops_spent,
            created_step=step,
            model_version=self.model_version,
        )
        self._next_id += 1
        self.records[record.id] = record
        self._vectors[record.id] = vector
        self._enforce_budget(step)
        return "quarantined" if record.id in self.records else "evicted"

    def ready_for_review(self) -> list[MemoryRecord]:
        return [
            r
            for r in self.records.values()
            if r.status == "quarantine" and r.support >= self.policy.min_support.get(r.verify_level, 1)
        ]

    def promote(self, record_id: int) -> None:
        self.records[record_id].status = "active"

    def reject(self, record_id: int) -> None:
        self.records.pop(record_id, None)
        self._vectors.pop(record_id, None)

    @contextmanager
    def trial(self, record_id: int):
        """Temporarily activate a quarantined record for shadow testing."""
        record = self.records[record_id]
        previous = record.status
        record.status = "active"
        try:
            yield
        finally:
            record.status = previous

    # ---- reading ------------------------------------------------------------

    def lookup(self, key: np.ndarray, *, step: int = 0, count: bool = True) -> Hint | None:
        vector = np.asarray(key, dtype=float)
        match = self._nearest(vector / np.linalg.norm(vector), statuses=("active",))
        if not match or match[1] < self.lookup_similarity:
            return None
        record, similarity = match
        if count:
            record.hits += 1
        return Hint(text=record.payload, similarity=similarity, record_id=record.id)

    def vector(self, record_id: int) -> np.ndarray:
        return self._vectors[record_id]

    def credit(self, record_id: int, loops_saved: float) -> None:
        if record_id in self.records:
            self.records[record_id].loops_saved += max(0.0, loops_saved)

    def _nearest(self, vector: np.ndarray, *, statuses: tuple[str, ...], payload: str | None = None):
        candidates = [
            r
            for r in self.records.values()
            if r.status in statuses
            and r.model_version == self.model_version
            and (payload is None or r.payload == payload)
        ]
        if not candidates:
            return None
        matrix = np.stack([self._vectors[r.id] for r in candidates])
        similarities = matrix @ vector
        best = int(np.argmax(similarities))
        return candidates[best], float(similarities[best])

    # ---- housekeeping -------------------------------------------------------

    def _value(self, record: MemoryRecord, step: int) -> float:
        usefulness = (record.hits + 1) * (record.loops_saved + record.loops_spent) * record.support
        age = max(0, step - record.created_step)
        return usefulness / record.nbytes / (1 + age / 100)

    def _enforce_budget(self, step: int) -> None:
        while self.records and self.used_bytes > self.budget_bytes:
            victim = min(self.records.values(), key=lambda r: self._value(r, step))
            self.reject(victim.id)

    def expire_quarantine(self, step: int, max_age: int) -> int:
        """Insights that never gathered enough support or evidence are dropped."""
        stale = [
            r.id for r in self.records.values() if r.status == "quarantine" and step - r.created_step > max_age
        ]
        for record_id in stale:
            self.reject(record_id)
        return len(stale)

    def drop_other_versions(self) -> int:
        """After a model update, old codes mean nothing to the new model."""
        stale = [r.id for r in self.records.values() if r.model_version != self.model_version]
        for record_id in stale:
            self.reject(record_id)
        return len(stale)

    def snapshot(self) -> dict:
        return copy.deepcopy({"records": self.records, "vectors": self._vectors, "next_id": self._next_id})

    def restore(self, snapshot: dict) -> None:
        state = copy.deepcopy(snapshot)
        self.records, self._vectors = state["records"], state["vectors"]
        # Ids keep increasing across rollbacks so audit logs never point at two records.
        self._next_id = max(self._next_id, state["next_id"])

    def stats(self) -> dict:
        statuses = [r.status for r in self.records.values()]
        return {
            "active": statuses.count("active"),
            "quarantine": statuses.count("quarantine"),
            "used_bytes": self.used_bytes,
            "budget_bytes": self.budget_bytes,
        }
