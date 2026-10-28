"""Interfaces every model backend implements. The pipeline only talks to these."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from mycelium.types import Answer, Hint, Problem


@dataclass
class RLCRSample:
    problem: Problem
    answer: Answer
    correct: bool
    reward: float
    advantage: float


class ModelBackend(Protocol):
    name: str
    # HIKMAT insights are only valid for the model version that produced them.
    version: str
    cost_per_loop: float

    def answer(
        self,
        problem: Problem,
        *,
        max_loops: int,
        hint: Hint | None = None,
        sample: int = 0,
        stop_at: float | None = None,
    ) -> Answer:
        """Answer with a confidence in [0, 1]. `sample` selects an independent attempt.

        The backend keeps looping until its confidence reaches `stop_at` (or its own
        default) or it runs out of loops, so callers can say how sure they need it to be.
        """
        ...


class TrainableBackend(ModelBackend, Protocol):
    def learn_sft(self, records: list[tuple[Problem, str]]) -> None:
        """Supervised fine-tuning on verified (problem, answer text) pairs."""
        ...

    def learn_rlcr(self, samples: list[RLCRSample]) -> None:
        """One policy update from RLCR-scored samples (GRPO-style advantages)."""
        ...
