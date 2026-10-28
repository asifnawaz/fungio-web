from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

DOMAINS = ("math", "code", "qa", "mcq")
MCQ_LETTERS = ("A", "B", "C", "D")


@dataclass(frozen=True)
class Problem:
    id: str
    domain: str
    prompt: str
    # Ground truth: a number for math, a test-suite source for code, a string for qa,
    # a letter for mcq. None means the question is unanswerable and the right move is
    # to abstain.
    answer: str | None
    difficulty: float
    family: str
    # Stand-in for the model's internal representation of the problem. Real backends
    # replace this with a pooled hidden state.
    features: np.ndarray = field(compare=False, repr=False)
    # Answer options for mcq problems, in letter order.
    choices: tuple[str, ...] = ()
    # Problems sharing a template are solved the same way with different numbers or names.
    # Empty means the problem is its own template (a unique question).
    template: str = ""

    @property
    def answerable(self) -> bool:
        return self.answer is not None

    @property
    def template_key(self) -> str:
        return self.template or self.id


@dataclass
class Answer:
    text: str
    confidence: float
    loops: int
    abstained: bool = False
    # Completion tokens reported by a real server; 0 when the backend doesn't count tokens.
    tokens: int = 0
    # Internal state at the end of reasoning; HIKMAT stores a compressed copy.
    latent: np.ndarray | None = field(default=None, repr=False)


@dataclass
class Hint:
    """What HIKMAT hands the model: a remembered verified method for a similar problem."""

    text: str
    similarity: float
    record_id: int
    # Template of the problem the insight was learned from, for measuring transfer.
    source: str = ""
