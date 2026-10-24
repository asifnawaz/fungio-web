"""Kill test for HIKMAT (spec 003): does a remembered, verified method help a real model?

GSM-Symbolic turns each of 100 GSM8K questions into a template with 50 variants (new names
and numbers, same reasoning). For every chosen template, variant 0 donates the insight:
its verified reference solution, which is what HIKMAT stores when the teacher solves a
hard problem. Variants 1..K are then solved three ways:

    none   no hint
    same   the insight from this template's variant 0
    other  the insight from a different template of the same step-count family

`same` vs `none` says whether a stored method helps on a new problem of its own kind.
`other` vs `none` says what a near miss in retrieval costs. Decision rules are fixed in
`specs/003-insight-kill-test/research.md` before any real run.

Works with any backend that has `answer(problem, max_loops=, hint=)`: a real model behind
`OpenAICompatBackend`, the simulated HTTP teacher, or the mock student (whose known
`hint_gain` and transfer the analysis must recover; see `tests/test_killtest.py`).
"""

from __future__ import annotations

import functools
import json
from concurrent.futures import ThreadPoolExecutor
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from mycelium.evals.datasets import stable_seed
from mycelium.evals.judges import judge
from mycelium.evals.real import load_gsm_symbolic, read_gsm_symbolic_rows
from mycelium.models.base import ModelBackend
from mycelium.models.mock import method_tag
from mycelium.types import Hint, Problem

CONDITIONS = ("none", "same", "other")
N_TEMPLATES = 100


@dataclass(frozen=True)
class Trial:
    template: int
    instance: int
    condition: str
    correct: bool
    # Completion tokens when the backend reports them, else reasoning loops.
    effort: float
    # Stand-in key similarity between the target and the donor (1.0 for `none`).
    similarity: float


@dataclass(frozen=True)
class Item:
    problem: Problem
    row: dict


@functools.lru_cache(maxsize=1)
def load_items() -> dict[tuple[int, int], Item]:
    problems = {p.id: p for p in load_gsm_symbolic()}
    return {
        (row["id"], row["instance"]): Item(problems[f"gsm-symbolic-{row['id']}-{row['instance']}"], row)
        for row in read_gsm_symbolic_rows()
    }


def choose_templates(n: int, seed: int = 0) -> list[int]:
    """A seeded sample, so a small run isn't biased toward the first templates in the file."""
    order = sorted(range(N_TEMPLATES), key=lambda t: stable_seed("killtest-templates", seed, t))
    return sorted(order[:n])


def other_donor(template: int, items: dict[tuple[int, int], Item], seed: int = 0) -> int:
    """Another template of the same step-count family; falls back to any other template."""
    family = items[(template, 0)].problem.family
    candidates = [t for t in range(N_TEMPLATES) if t != template and items[(t, 0)].problem.family == family]
    pool = candidates or [t for t in range(N_TEMPLATES) if t != template]
    return min(pool, key=lambda t: stable_seed("killtest-other", seed, template, t))


def solution_payload(donor: Item) -> str:
    """What a real model sees: the donor problem and its verified worked solution."""
    return f"Problem: {donor.row['question']}\nVerified solution:\n{donor.row['answer']}"


def tag_payload(donor: Item) -> str:
    """What the mock student understands: the method tag of the donor's family."""
    return method_tag(donor.problem.family)


def run(
    backend: ModelBackend,
    *,
    templates: Iterable[int],
    variants: int = 10,
    payload: Callable[[Item], str] = solution_payload,
    max_loops: int = 8,
    seed: int = 0,
    conditions: tuple[str, ...] = CONDITIONS,
    trials_path: Path | None = None,
    on_trial: Callable[[Trial], None] | None = None,
    workers: int = 1,
) -> list[Trial]:
    """Solve every (target, condition) pair once. With `trials_path`, finished trials are
    appended as JSON lines and skipped on a rerun, so a long GPU run can resume.
    `workers` > 1 sends that many requests at once (match the server's `-np` slots)."""
    items = load_items()
    done: dict[tuple[int, int, str], Trial] = {}
    if trials_path is not None and trials_path.exists():
        for line in trials_path.read_text().splitlines():
            if line.strip():
                trial = Trial(**json.loads(line))
                done[(trial.template, trial.instance, trial.condition)] = trial
    todo = []
    for template in templates:
        donors = {"same": items[(template, 0)], "other": items[(other_donor(template, items, seed), 0)]}
        for instance in range(1, variants + 1):
            for condition in conditions:
                todo.append((template, instance, condition, donors))

    def solve(job) -> Trial:
        template, instance, condition, donors = job
        target = items[(template, instance)]
        hint, similarity = None, 1.0
        if condition != "none":
            donor = donors[condition]
            similarity = float(target.problem.features @ donor.problem.features)
            hint = Hint(text=payload(donor), similarity=similarity, record_id=-1, source=donor.problem.template_key)
        answer = backend.answer(target.problem, max_loops=max_loops, hint=hint)
        return Trial(
            template=template,
            instance=instance,
            condition=condition,
            correct=judge(target.problem, answer),
            effort=float(answer.tokens or answer.loops),
            similarity=similarity,
        )

    pending = [job for job in todo if job[:3] not in done]
    fresh: dict[tuple[int, int, str], Trial] = {}
    out = open(trials_path, "a") if trials_path is not None else None  # noqa: SIM115
    try:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            # map keeps input order, so the trials file is written in a stable order.
            for job, trial in zip(pending, pool.map(solve, pending), strict=True):
                fresh[job[:3]] = trial
                if out is not None:
                    out.write(json.dumps(asdict(trial)) + "\n")
                    out.flush()
                if on_trial is not None:
                    on_trial(trial)
    finally:
        if out is not None:
            out.close()
    trials = [done.get(job[:3]) or fresh[job[:3]] for job in todo]
    return trials


# ---- analysis -----------------------------------------------------------------


def _paired(trials: list[Trial]) -> dict[int, dict[str, np.ndarray]]:
    """Per template: arrays of (correct, effort) per condition, aligned by instance."""
    by_template: dict[int, dict[str, dict[int, Trial]]] = {}
    for t in trials:
        by_template.setdefault(t.template, {}).setdefault(t.condition, {})[t.instance] = t
    paired = {}
    for template, conds in by_template.items():
        instances = sorted(set.intersection(*(set(conds.get(c, {})) for c in CONDITIONS)))
        if instances:
            paired[template] = {
                c: np.array([[conds[c][i].correct, conds[c][i].effort] for i in instances], dtype=float)
                for c in CONDITIONS
            }
    return paired


def analyze(trials: list[Trial], *, seed: int = 0, boot: int = 2000, fit: bool = True) -> dict:
    """Accuracy and effort per condition, paired differences with 95% intervals from a
    bootstrap over templates (variants of one template are not independent), the
    equivalent mock parameters, and the pre-registered verdict."""
    paired = _paired(trials)
    if not paired:
        raise ValueError("no complete (none, same, other) triples to analyze")
    templates = sorted(paired)

    def stats(sample: list[int]) -> dict[str, float]:
        rows = {c: np.concatenate([paired[t][c] for t in sample]) for c in CONDITIONS}
        acc = {c: rows[c][:, 0].mean() for c in CONDITIONS}
        effort = {c: rows[c][:, 1].mean() for c in CONDITIONS}
        return {
            **{f"acc_{c}": acc[c] for c in CONDITIONS},
            **{f"effort_{c}": effort[c] for c in CONDITIONS},
            "d_acc_same": acc["same"] - acc["none"],
            "d_acc_other": acc["other"] - acc["none"],
            "d_effort_same": (effort["same"] - effort["none"]) / effort["none"],
            "d_effort_other": (effort["other"] - effort["none"]) / effort["none"],
        }

    point = stats(templates)
    rng = np.random.default_rng(seed)
    draws = [stats(list(rng.choice(templates, size=len(templates)))) for _ in range(boot)]
    ci = {
        k: (float(np.percentile([d[k] for d in draws], 2.5)), float(np.percentile([d[k] for d in draws], 97.5)))
        for k in ("d_acc_same", "d_acc_other", "d_effort_same", "d_effort_other")
    }

    return {
        "templates": len(templates),
        "targets": sum(len(paired[t]["none"]) for t in templates),
        **{k: float(v) for k, v in point.items()},
        "ci95": ci,
        "mock_equivalents": fit_mock(point, ci, population=(templates, max(t.instance for t in trials))) if fit else None,
        "verdict": verdict(point, ci),
    }


def _accuracy(student, condition: str, population: tuple[list[int], int], seeds: int = 5) -> float:
    """Mock accuracy on exactly the measured problems, averaged over several mock seeds so
    it is a smooth function of the parameters (the mock draws outcomes per problem and seed)."""
    templates, variants = population
    correct = []
    for seed in range(seeds):
        student.seed = seed
        trials = run(student, templates=templates, variants=variants, payload=tag_payload, conditions=(condition,))
        correct += [t.correct for t in trials]
    return float(np.mean(correct))


def _bisect(f: Callable[[float], float], target: float, lo: float, hi: float, iters: int) -> float:
    """x in [lo, hi] where the increasing function f reaches target (clamped to the ends)."""
    for _ in range(iters):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(mid) < target else (lo, mid)
    return (lo + hi) / 2


def fit_mock(
    point: dict, ci: dict | None = None, *, population: tuple[list[int], int], iters: int = 12
) -> dict:
    """The mock parameters that reproduce the measured accuracies.

    One at a time: the student's math skill to match `none`, then `hint_gain` to match
    `same`, then `procedural_transfer` to match `other`. Each accuracy rises with its
    parameter, so bisection works. The mock runs on the measured problems (`population` =
    templates and variants per template), so the mix of problems matches. With `ci`, the ends of
    the 95% interval of `same - none` give an interval for `hint_gain` (it ignores the
    error in the fitted skill, so treat it as a lower bound on the uncertainty). The result plugs into
    `python -m mycelium.cli insights --gain G --transfer T` to see what the effect is worth.
    Effort isn't fitted: the mock counts loops, real models count tokens.
    """
    from mycelium.pipeline import make_student

    def student(skill: float, gain: float = 0.0, transfer: float = 0.0):
        model = make_student(hint_gain=gain, procedural_transfer=transfer)
        model.skill["math"] = skill
        return model

    skill = _bisect(lambda s: _accuracy(student(s), "none", population), point["acc_none"], -0.5, 2.0, iters)
    # Match differences, not levels: an error in the fitted skill then mostly cancels.
    base = _accuracy(student(skill), "none", population)

    def fit_gain(d_acc_same: float) -> float:
        return _bisect(lambda g: _accuracy(student(skill, g), "same", population) - base, d_acc_same, -1.0, 1.5, iters)

    gain = fit_gain(point["d_acc_same"])
    gain_ci = tuple(fit_gain(d) for d in ci["d_acc_same"]) if ci is not None else None
    transfer = None
    if abs(gain) > 0.02:
        # The mock scales a near-miss hint by gain x transfer; flip the sign so the bisected
        # function rises. transfer < 0 means a near-miss hint hurts.
        sign = 1 if gain > 0 else -1
        transfer = _bisect(
            lambda t: sign * (_accuracy(student(skill, gain, t), "other", population) - base),
            sign * point["d_acc_other"], -3.0, 1.5, iters,
        )
    return {"math_skill": skill, "hint_gain": gain, "hint_gain_ci95": gain_ci, "procedural_transfer": transfer}


def verdict(point: dict, ci: dict) -> str:
    """Pre-registered in specs/003-insight-kill-test/research.md; change it there first."""
    acc_lo, acc_hi = ci["d_acc_same"]
    effort_lo, effort_hi = ci["d_effort_same"]
    if acc_lo > 0 or (point["d_effort_same"] <= -0.10 and effort_hi < 0 and acc_lo >= -0.02):
        return "pays"
    # Significantly more wrong answers is harm, however many tokens it saves.
    if acc_hi < 0 or (acc_hi <= 0.02 and effort_lo >= -0.05):
        return "kill"
    return "inconclusive"


def format_report(report: dict, effort_unit: str) -> str:
    ci = report["ci95"]
    lines = [
        f"templates {report['templates']}, targets {report['targets']} (each solved 3 ways)",
        f"{'condition':<9} {'accuracy':>8} {'mean ' + effort_unit:>14}",
    ]
    for c in CONDITIONS:
        lines.append(f"{c:<9} {report['acc_' + c]:>8.3f} {report['effort_' + c]:>14.1f}")
    for c in ("same", "other"):
        lines.append(
            f"{c} - none: accuracy {report['d_acc_' + c]:+.3f} [{ci['d_acc_' + c][0]:+.3f}, {ci['d_acc_' + c][1]:+.3f}], "
            f"{effort_unit} {report['d_effort_' + c]:+.1%} [{ci['d_effort_' + c][0]:+.1%}, {ci['d_effort_' + c][1]:+.1%}]"
        )
    eq = report["mock_equivalents"]
    if eq is not None:
        transfer = "n/a" if eq["procedural_transfer"] is None else f"{eq['procedural_transfer']:.2f}"
        interval = "" if eq["hint_gain_ci95"] is None else " [{:.2f}, {:.2f}]".format(*eq["hint_gain_ci95"])
        lines.append(f"mock equivalents: hint_gain {eq['hint_gain']:.2f}{interval}, procedural_transfer {transfer}")
    lines.append(f"verdict: {report['verdict']}")
    return "\n".join(lines)
