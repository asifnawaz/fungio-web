"""Does HIKMAT memory help, and when? A sweep over the assumptions the mock makes.

The mock student is told how much a hint helps (`hint_gain`) and how much of that carries
to a different problem of the same family (`procedural_transfer`). Those two numbers are
assumptions, not measurements, so a single run can only show the plumbing works. This
sweep runs the whole pipeline over a grid of them and reports what memory adds compared
with the same router without memory. The result tells you which effect size a real model
must show for memory to pay off; spec 002 measures the real effect.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from mycelium.pipeline import E2EConfig, run_e2e

DEFAULT_GAINS = (-0.2, 0.0, 0.1, 0.2, 0.4)
DEFAULT_TRANSFERS = (0.0, 0.25, 0.5)


def summarize(report: dict) -> dict:
    """Memory's effect over days 1+ (day 0 starts with empty memory)."""
    days = report["p4_hikmat"]["days"][1:]
    hits: dict[str, int] = {}
    for day in days:
        for kind, n in day["retrieval"].items():
            hits[kind] = hits.get(kind, 0) + n
    total = sum(hits.get(k, 0) for k in ("same_template", "same_family_only", "other_family"))

    def mean(key: str) -> float:
        return float(np.mean([d[key] for d in days]))

    return {
        "accuracy": mean("accuracy"),
        "cost": mean("mean_cost"),
        "memory_accuracy_gain": mean("accuracy") - mean("no_memory_accuracy"),
        "memory_cost_saving": mean("no_memory_cost") - mean("mean_cost"),
        "teacher_only_accuracy": mean("teacher_only_accuracy"),
        "teacher_only_cost": mean("teacher_only_cost"),
        "repeat_rate": mean("repeat_rate"),
        "hints": total,
        "same_template_share": hits.get("same_template", 0) / total if total else 0.0,
        "promoted": sum(d["decisions"].get("promoted", 0) for d in report["p4_hikmat"]["days"]),
        "rollbacks": sum(d["rolled_back"] for d in report["p4_hikmat"]["days"]),
    }


def sweep(
    base: E2EConfig = E2EConfig(),
    gains: tuple[float, ...] = DEFAULT_GAINS,
    transfers: tuple[float, ...] = DEFAULT_TRANSFERS,
) -> list[dict]:
    rows = []
    for gain in gains:
        for transfer in transfers:
            config = replace(base, hint_gain=gain, procedural_transfer=transfer)
            rows.append({"hint_gain": gain, "procedural_transfer": transfer, **summarize(run_e2e(config))})
    return rows


def format_rows(rows: list[dict]) -> str:
    header = (
        f"{'gain':>5} {'transfer':>8} {'acc':>6} {'no-mem Δacc':>11} {'cost':>6} {'no-mem Δcost':>12} "
        f"{'teacher acc/cost':>16} {'hints':>5} {'same-tmpl':>9} {'promoted':>8} {'repeat':>6}"
    )
    lines = [header]
    for r in rows:
        lines.append(
            f"{r['hint_gain']:>5.2f} {r['procedural_transfer']:>8.2f} {r['accuracy']:>6.3f} "
            f"{r['memory_accuracy_gain']:>+11.3f} {r['cost']:>6.1f} {r['memory_cost_saving']:>+12.1f} "
            f"{r['teacher_only_accuracy']:>9.3f}/{r['teacher_only_cost']:<6.1f} {r['hints']:>5} "
            f"{r['same_template_share']:>9.2f} {r['promoted']:>8} {r['repeat_rate']:>6.2f}"
        )
    return "\n".join(lines)
