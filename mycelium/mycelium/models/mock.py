"""Mock backend: a small simulated model with the failure modes the pipeline must fix.

The simulated student starts overconfident, unaware of what it cannot know, and weak in
some domains. Distillation raises its skill, RLCR fixes its confidence, and HIKMAT hints
let it stop thinking early on problem types it has already solved. Outcomes are seeded
per (problem, attempt), so runs are reproducible and more loops never hurt.

None of the numbers here say anything about real models. They exist so the plumbing,
the gates and the safety checks can be tested end to end.
"""

from __future__ import annotations

import math

import numpy as np

from mycelium.evals.datasets import CODE_TASKS, fake_name, stable_seed
from mycelium.models.base import RLCRSample
from mycelium.types import DOMAINS, MCQ_LETTERS, Answer, Hint, Problem

SFT_CEILING = 0.85
DEFAULT_FAMILY_TRANSFER = {"math": 0.25, "code": 0.25, "qa": 0.0, "mcq": 0.0}


def method_tag(family: str) -> str:
    """The mock payload of an insight: which solution method worked for this family."""
    return f"method:{family}"


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


class MockModel:
    def __init__(
        self,
        name: str,
        skill: dict[str, float],
        *,
        overconfidence: float,
        awareness: float,
        cost_per_loop: float,
        version: str = "mock-v0.1",
        seed: int = 0,
        loop_gain: float = 0.05,
        known_bonus: float = 0.15,
        hint_gain: float = 0.4,
        misleading_penalty: float = 0.6,
        conf_noise: float = 0.06,
        stop_confidence: float = 0.85,
        family_skill: dict[str, float] | None = None,
        dunning_kruger: float = 0.0,
        family_transfer: dict[str, float] | None = None,
    ):
        assert set(skill) == set(DOMAINS)
        self.name = name
        self.version = version
        self.cost_per_loop = cost_per_loop
        self.skill = dict(skill)
        # Per-subject offsets on top of the domain skill (e.g. weak in chemistry).
        self.family_skill = dict(family_skill or {})
        # Extra overconfidence where the model is weak: the less it knows, the less it
        # knows that it doesn't know.
        self.dunning_kruger = dunning_kruger
        self.overconfidence = overconfidence
        self.awareness = awareness
        self.knowledge: set[str] = set()
        self.seed = seed
        self.loop_gain = loop_gain
        self.known_bonus = known_bonus
        self.hint_gain = hint_gain
        # A hint for the wrong kind of problem always hurts, whatever `hint_gain` assumes.
        self.misleading_penalty = misleading_penalty
        # How much of a hint's benefit carries to a *different* problem of the same family.
        # Procedures (math, code) partly transfer; facts (qa, mcq) don't: knowing one
        # astronomy answer doesn't answer another astronomy question.
        self.family_transfer = dict(family_transfer or DEFAULT_FAMILY_TRANSFER)
        self.conf_noise = conf_noise
        self.stop_confidence = stop_confidence

    # ---- inference ----------------------------------------------------------

    def p_correct(self, problem: Problem, loops: int, hint: Hint | None = None) -> float:
        if not problem.answerable:
            return 0.0
        x = self.skill[problem.domain] - problem.difficulty + self.loop_gain * (loops - 1)
        x += self.family_skill.get(problem.family, 0.0)
        if problem.family in self.knowledge:
            x += self.known_bonus
        if hint is not None:
            x += hint.similarity * self.hint_shift(problem, hint)
        return _sigmoid(6 * x)

    def hint_shift(self, problem: Problem, hint: Hint) -> float:
        """Skill shift per unit of similarity: the full `hint_gain` for an insight from the
        same template, the domain's transfer fraction of it for another problem of the
        same family, and a fixed penalty for a different family (misleading)."""
        if hint.text != method_tag(problem.family):
            return -self.misleading_penalty
        if not hint.source or hint.source == problem.template_key:
            return self.hint_gain
        return self.hint_gain * self.family_transfer.get(problem.domain, 0.0)

    def _confidence(self, problem: Problem, p: float, z: float) -> float:
        if problem.answerable:
            weakness = max(0.0, -self.family_skill.get(problem.family, 0.0))
            raw = p + self.overconfidence + self.dunning_kruger * weakness
        else:
            naive = _sigmoid(6 * (self.skill[problem.domain] - problem.difficulty))
            raw = (1 - self.awareness) * (naive + self.overconfidence) + self.awareness * 0.05
        return float(np.clip(raw + self.conf_noise * z, 0.02, 0.98))

    def answer(
        self,
        problem: Problem,
        *,
        max_loops: int,
        hint: Hint | None = None,
        sample: int = 0,
        stop_at: float | None = None,
    ) -> Answer:
        rng = np.random.default_rng(stable_seed(self.name, self.seed, problem.id, sample))
        u, z = rng.random(), rng.normal()
        target = self.stop_confidence if stop_at is None else stop_at
        loops = 1
        while True:
            p = self.p_correct(problem, loops, hint)
            confidence = self._confidence(problem, p, z)
            if confidence >= target or loops >= max_loops:
                break
            loops += 1
        correct = problem.answerable and u < p
        return Answer(
            text=self._render(problem, correct, rng),
            confidence=confidence,
            loops=loops,
            latent=problem.features.copy(),
        )

    def _render(self, problem: Problem, correct: bool, rng: np.random.Generator) -> str:
        if problem.domain == "math":
            value = int(problem.answer)
            return str(value if correct else value + int(rng.choice([-10, -2, -1, 1, 3, 7])))
        if problem.domain == "code":
            task = CODE_TASKS[problem.family.split(":", 1)[1]]
            return task.solution if correct else task.buggy
        if problem.domain == "mcq":
            if correct:
                return problem.answer
            # Wrong answers cluster on one attractive distractor, as with real students.
            wrong = [letter for letter in MCQ_LETTERS[: len(problem.choices)] if letter != problem.answer]
            attractive = wrong[stable_seed("distractor", problem.id) % len(wrong)]
            return attractive if rng.random() < 0.6 else str(rng.choice(wrong))
        return problem.answer if correct else fake_name(rng, 2)

    # ---- training -----------------------------------------------------------

    def learn_sft(self, records: list[tuple[Problem, str]]) -> None:
        for domain in DOMAINS:
            n = sum(1 for p, _ in records if p.domain == domain)
            gain = 0.35 * (1 - math.exp(-n / 150))
            self.skill[domain] += gain * max(0.0, SFT_CEILING - self.skill[domain])
        self.knowledge.update(p.family for p, _ in records)

    def learn_rlcr(self, samples: list[RLCRSample], lr: float = 0.5) -> None:
        # Mock policy update: move stated confidence toward empirical correctness, which
        # is what the Brier term in the RLCR reward pushes a real policy to do.
        answerable = [s for s in samples if s.problem.answerable]
        unanswerable = [s for s in samples if not s.problem.answerable]
        if answerable:
            gap = np.mean([s.answer.confidence - float(s.correct) for s in answerable])
            self.overconfidence -= lr * gap
            weak = [s for s in answerable if self.family_skill.get(s.problem.family, 0.0) < 0]
            if weak:
                weak_gap = np.mean([s.answer.confidence - float(s.correct) for s in weak])
                self.dunning_kruger = max(0.0, self.dunning_kruger - lr * weak_gap)
        if unanswerable:
            stated = np.mean([s.answer.confidence for s in unanswerable])
            self.awareness = float(np.clip(self.awareness + lr * stated, 0.0, 1.0))
