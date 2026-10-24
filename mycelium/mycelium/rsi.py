"""RSI: recursive self-improvement of the model's weights, behind the same kind of gates
as the memory autopilot.

One generation:
  1. Propose fresh problems with checkable answers (math, code: never facts, which have no
     source to verify against).
  2. The model attempts each a few times; keep the ones at its frontier (success rate in
     the recipe's band).
  3. Keep only traces JUDGE verifies, mix in some verified teacher traces as an anchor.
  4. Train a *copy* of the model on them.
  5. Promote the copy only if it is better on the exam (golden set + held-out problems the
     loop never trains on) by more than noise, without hallucinating more.
  6. Stop on a plateau, or when self-made problems improve but the exam doesn't (Goodhart).

The recursive part: the loop also improves its own method. Each recipe (difficulty band,
breadth) is scored by the exam gain it produced, and a UCB bandit picks the next one. What
the loop may never change: JUDGE, the golden set (fingerprinted), the exam and the gates.

Published precedents: STaR (arXiv 2203.14465) trains on its own verified rationales;
Absolute Zero (arXiv 2505.03335) proposes and solves its own code-verified tasks. Model
collapse from training on unverified self-generated data is the known failure; the
verification and the exam gate are there for it.
"""

from __future__ import annotations

import copy
import math
from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np

from mycelium.autopilot import GoldenSet
from mycelium.evals.harness import evaluate
from mycelium.evals.judges import judge
from mycelium.models.mock import MockModel
from mycelium.types import Problem

VERIFIABLE_DOMAINS = ("math", "code")


@dataclass(frozen=True)
class Recipe:
    name: str
    # Keep problems whose estimated success rate falls in this band.
    band: tuple[float, float]
    # "broad": all families; "weakest": only the three families it solves least often.
    focus: str = "broad"


RECIPES = (
    Recipe("frontier", (0.25, 0.8)),
    Recipe("hard", (0.05, 0.5)),
    Recipe("easy", (0.75, 1.0)),
    Recipe("weakest-first", (0.25, 0.8), "weakest"),
)


@dataclass
class RSIConfig:
    generations: int = 8
    proposals: int = 240  # problems proposed per generation
    attempts: int = 4  # tries per problem: estimates the success rate and yields traces
    anchor: int = 60  # verified teacher traces mixed into every generation
    # "judge": keep traces JUDGE verifies. Test settings: "off" keeps every trace (a broken
    # verifier), "inverted" keeps only wrong ones (the worst case the exam gate must stop).
    verify: str = "judge"
    patience: int = 3  # stop after this many generations in a row without a promotion
    goodhart_strikes: int = 2  # stop after this many in a row of self-gain without exam gain
    max_hallucination_rise: float = 0.01
    seed: int = 0
    recipes: tuple[Recipe, ...] = RECIPES


@dataclass
class _Bandit:
    recipes: tuple[Recipe, ...]
    pulls: dict[str, int] = field(default_factory=dict)
    total: dict[str, float] = field(default_factory=dict)

    def choose(self) -> Recipe:
        for recipe in self.recipes:
            if self.pulls.get(recipe.name, 0) == 0:
                return recipe
        n = sum(self.pulls.values())
        return max(
            self.recipes,
            key=lambda r: self.total[r.name] / self.pulls[r.name] + 0.05 * math.sqrt(2 * math.log(n) / self.pulls[r.name]),
        )

    def update(self, recipe: Recipe, reward: float) -> None:
        self.pulls[recipe.name] = self.pulls.get(recipe.name, 0) + 1
        self.total[recipe.name] = self.total.get(recipe.name, 0.0) + reward


def _paired_gain(before: np.ndarray, after: np.ndarray, *, seed: int, boot: int = 1000) -> tuple[float, float]:
    """Mean accuracy gain and the 2.5th percentile of a paired bootstrap over problems."""
    diff = after.astype(float) - before.astype(float)
    rng = np.random.default_rng(seed)
    draws = [diff[rng.integers(0, len(diff), len(diff))].mean() for _ in range(boot)]
    return float(diff.mean()), float(np.percentile(draws, 2.5))


class RSILoop:
    def __init__(
        self,
        model: MockModel,
        golden: GoldenSet,
        heldout: list[Problem],
        anchor: list[tuple[Problem, str]],
        propose: Callable[[int, int], list[Problem]],
        config: RSIConfig = RSIConfig(),
    ):
        self.model = model
        self.golden = golden
        self.heldout = heldout
        self.anchor = anchor
        self.propose = propose
        self.config = config
        self.bandit = _Bandit(config.recipes)
        self._exam_ids = {p.id for p in golden.problems} | {p.id for p in heldout}

    def exam(self) -> list[Problem]:
        # Reading the golden set re-checks its fingerprint (TamperError if anything changed).
        return list(self.golden.problems) + self.heldout

    @staticmethod
    def _evaluate(model: MockModel, problems: list[Problem]) -> dict:
        return evaluate(lambda p: model.answer(p, max_loops=4), problems)

    def _correct(self, model: MockModel, problems: list[Problem]) -> np.ndarray:
        return np.array([judge(p, model.answer(p, max_loops=4)) for p in problems])

    def _frontier(self, recipe: Recipe, generation: int) -> tuple[list[Problem], list[tuple[Problem, str]], dict]:
        cfg = self.config
        proposed = [p for p in self.propose(cfg.seed * 1000 + generation, cfg.proposals) if p.domain in VERIFIABLE_DOMAINS]
        if self._exam_ids & {p.id for p in proposed}:
            raise ValueError("proposed problems overlap the exam; the loop must never train on it")
        attempts: dict[str, list] = {}
        for p in proposed:
            answers = [self.model.answer(p, max_loops=4, sample=1 + s) for s in range(cfg.attempts)]
            attempts[p.id] = [(a, judge(p, a)) for a in answers]
        rate = {pid: np.mean([c for _, c in tries]) for pid, tries in attempts.items()}
        lo, hi = recipe.band
        kept = [p for p in proposed if lo <= rate[p.id] <= hi]
        if recipe.focus == "weakest":
            by_family: dict[str, list[float]] = {}
            for p in proposed:
                by_family.setdefault(p.family, []).append(rate[p.id])
            weakest = set(sorted(by_family, key=lambda f: np.mean(by_family[f]))[:3])
            kept = [p for p in kept if p.family in weakest]
        keep = {"judge": lambda c: c, "off": lambda c: True, "inverted": lambda c: not c}[cfg.verify]
        traces = [(p, a.text) for p in kept for a, correct in attempts[p.id] if keep(correct)]
        wrong = sum(not correct for p in kept for _, correct in attempts[p.id] if keep(correct))
        stats = {"proposed": len(proposed), "kept": len(kept), "traces": len(traces), "wrong_traces": wrong}
        return kept, traces, stats

    def run(self) -> dict:
        cfg = self.config
        start = self._evaluate(self.model, self.exam())
        generations, misses, strikes, stop = [], 0, 0, "budget"
        for g in range(cfg.generations):
            recipe = self.bandit.choose()
            kept, traces, stats = self._frontier(recipe, g)
            rng = np.random.default_rng(cfg.seed * 7919 + g)
            anchor = [self.anchor[i] for i in rng.choice(len(self.anchor), size=min(cfg.anchor, len(self.anchor)), replace=False)]
            candidate = copy.deepcopy(self.model)
            candidate.learn_self_play(traces + anchor)

            exam = self.exam()
            gain, lower = _paired_gain(self._correct(self.model, exam), self._correct(candidate, exam), seed=cfg.seed + g)
            self_gain = (
                float(self._correct(candidate, kept).mean() - self._correct(self.model, kept).mean()) if kept else 0.0
            )
            before, after = self._evaluate(self.model, exam), self._evaluate(candidate, exam)
            honest = after["hallucination_rate"] <= before["hallucination_rate"] + cfg.max_hallucination_rise
            promoted = lower > 0 and honest
            if promoted:
                candidate.version = f"{self.model.version}+rsi{g}"
                self.model = candidate
            self.bandit.update(recipe, gain)
            misses = 0 if promoted else misses + 1
            strikes = strikes + 1 if (self_gain > 0.02 and gain <= 0) else 0
            generations.append({
                "generation": g, "recipe": recipe.name, **stats,
                "exam_gain": gain, "exam_gain_lower95": lower, "self_gain": self_gain,
                "hallucination": (before["hallucination_rate"], after["hallucination_rate"]),
                "promoted": promoted, "version": self.model.version,
            })
            if strikes >= cfg.goodhart_strikes:
                stop = "goodhart"
                break
            if misses >= cfg.patience:
                stop = "plateau"
                break
        end = self._evaluate(self.model, self.exam())
        return {
            "start": start, "end": end, "stop": stop, "generations": generations,
            "recipes": {name: {"pulls": n, "mean_exam_gain": self.bandit.total[name] / n}
                        for name, n in self.bandit.pulls.items()},
        }


def run_rsi(config: RSIConfig = RSIConfig(), *, families: dict[str, list[str]] | None = None) -> dict:
    """Synthetic suite: distill a mock student from the mock teacher (P1), then run RSI.

    `families` restricts what the proposer can generate (a narrow proposer is how the
    Goodhart test is built)."""
    from mycelium.distill import build_distillation_set
    from mycelium.evals.datasets import make_suite
    from mycelium.pipeline import E2EConfig, build_synthetic_suite, make_student, make_teacher

    suite = build_synthetic_suite(E2EConfig(seed=config.seed))
    teacher, student = make_teacher(), make_student()
    anchor = build_distillation_set(teacher, suite.train)
    student.learn_sft(anchor)
    heldout = [p for p in suite.test if p.domain in VERIFIABLE_DOMAINS]
    golden = GoldenSet([p for p in suite.golden if p.domain in VERIFIABLE_DOMAINS])

    def propose(seed: int, n: int) -> list[Problem]:
        # Fresh seeds far from the suite's, so proposals never collide with exam ids.
        return make_suite(10_000 + seed, n // 2, families=families)

    loop = RSILoop(student, golden, heldout, [r for r in anchor if r[0].domain in VERIFIABLE_DOMAINS], propose, config)
    return loop.run()


def format_rsi(report: dict) -> str:
    lines = [f"{'gen':>3} {'recipe':<14} {'kept':>5} {'traces':>6} {'wrong':>5} {'exam gain [lo95]':>18} {'self gain':>9}  promoted"]
    for g in report["generations"]:
        lines.append(
            f"{g['generation']:>3} {g['recipe']:<14} {g['kept']:>5} {g['traces']:>6} {g['wrong_traces']:>5} "
            f"{g['exam_gain']:>+8.3f} [{g['exam_gain_lower95']:+.3f}] {g['self_gain']:>+9.3f}  {g['promoted']}"
        )
    s, e = report["start"], report["end"]
    lines.append(
        f"exam accuracy {s['accuracy']:.3f} -> {e['accuracy']:.3f}, ECE {s['ece']:.3f} -> {e['ece']:.3f}, "
        f"hallucination {s['hallucination_rate']:.3f} -> {e['hallucination_rate']:.3f}; stopped: {report['stop']}"
    )
    return "\n".join(lines)
