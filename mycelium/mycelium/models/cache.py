"""Memoize a backend's answers.

Threshold tuning replays the same problems through many router settings, so without a
cache a real teacher would be asked the same question hundreds of times. Answers are
keyed by everything that changes the request; each attempt (`sample`) stays distinct.
"""

from __future__ import annotations

from mycelium.models.base import ModelBackend
from mycelium.types import Answer, Hint, Problem


class CachedBackend:
    def __init__(self, backend: ModelBackend):
        self.backend = backend
        self.name = backend.name
        self.version = backend.version
        self.cost_per_loop = backend.cost_per_loop
        self._cache: dict[tuple, Answer] = {}
        self.hits = 0
        self.misses = 0

    def answer(
        self,
        problem: Problem,
        *,
        max_loops: int,
        hint: Hint | None = None,
        sample: int = 0,
        stop_at: float | None = None,
    ) -> Answer:
        key = (problem.id, max_loops, hint.text if hint else None, sample, stop_at)
        if key in self._cache:
            self.hits += 1
        else:
            self.misses += 1
            self._cache[key] = self.backend.answer(
                problem, max_loops=max_loops, hint=hint, sample=sample, stop_at=stop_at
            )
        return self._cache[key]
