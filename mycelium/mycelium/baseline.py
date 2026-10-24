"""`python -m mycelium.cli baseline`: measure one model alone before anything is trained.

This is P0 on real hardware: the small student (or any model behind an OpenAI-compatible
server) answers the holdout of a real suite, and we record accuracy, calibration,
hallucination and abstention per domain, plus speed. Every later stage is compared with
these numbers, so they come first.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor

from mycelium.evals.harness import evaluate
from mycelium.models.base import ModelBackend
from mycelium.models.openai_compat import DEFAULT_CONFIDENCE
from mycelium.pipeline import E2EConfig, build_real_suite
from mycelium.types import Answer, Problem


def run_baseline(backend: ModelBackend, config: E2EConfig, *, max_loops: int = 1, workers: int = 1) -> dict:
    """Evaluate `backend` on the suite's holdout (tune + test), never on the golden set."""
    suite = build_real_suite(config)
    return evaluate_problems(backend, suite.tune + suite.test, label=config.suite, max_loops=max_loops, workers=workers)


def evaluate_problems(
    backend: ModelBackend, holdout: list[Problem], *, label: str, max_loops: int = 1, workers: int = 1
) -> dict:
    """Answer every problem once and report metrics per domain plus speed.

    `workers` > 1 sends that many requests at once; a llama-server with as many slots
    (`-np`) batches them, which on a CPU raises total tokens/s a lot.
    """
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda p: backend.answer(p, max_loops=max_loops), holdout))
    seconds = time.perf_counter() - start
    answers: dict[str, Answer] = {p.id: a for p, a in zip(holdout, results, strict=True)}
    overall = evaluate(lambda p: answers[p.id], holdout)
    by_domain = {}
    for domain in sorted({p.domain for p in holdout}):
        subset = [p for p in holdout if p.domain == domain]
        by_domain[domain] = evaluate(lambda p: answers[p.id], subset)
    tokens = sum(a.tokens for a in answers.values())
    return {
        "suite": label,
        "model": getattr(backend, "name", "unknown"),
        "overall": overall,
        "by_domain": by_domain,
        # The parser falls back to exactly this value when the CONFIDENCE line is missing,
        # so this share is an upper bound on format failures.
        "default_confidence_share": sum(a.confidence == DEFAULT_CONFIDENCE for a in answers.values()) / len(answers),
        "seconds": seconds,
        "tokens": tokens,
        "tokens_per_second": tokens / seconds if seconds and tokens else None,
        "workers": workers,
    }


def format_baseline(report: dict) -> str:
    lines = [
        f"{report['model']} on {report['suite']} ({report['overall']['n']} questions)",
        f"{'domain':<8} {'n':>4} {'acc':>6} {'ECE':>6} {'halluc':>7} {'abstain':>8}",
    ]
    for name, m in [("all", report["overall"]), *report["by_domain"].items()]:
        lines.append(
            f"{name:<8} {m['n']:>4} {m['accuracy']:>6.3f} {m['ece']:>6.3f} {m['hallucination_rate']:>7.3f} {m['abstain_rate']:>8.3f}"
        )
    speed = "n/a" if report["tokens_per_second"] is None else f"{report['tokens_per_second']:.1f} tokens/s total"
    lines.append(f"time {report['seconds']:.0f} s, {speed}; confidence exactly 0.5 (format failure?) "
                 f"{report['default_confidence_share']:.1%}")
    return "\n".join(lines)
