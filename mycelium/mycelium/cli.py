"""Command line entry: `python -m mycelium.cli e2e --out report.json`."""

from __future__ import annotations

import argparse
import json
import os

from mycelium import insights
from mycelium.bench import benchmark, format_rows
from mycelium.models.openai_compat import OpenAICompatBackend
from mycelium.pipeline import E2EConfig, run_e2e
from mycelium.sim_teacher import SimConfig, make_server

INDEX_KINDS = ["numpy", "binary-ivf", "faiss-hnsw"]


def _summary(report: dict) -> str:
    p0, p1, p2, p3 = (report[k] for k in ("p0_baseline", "p1_distill", "p2_rlcr", "p3_triage"))
    lines = [
        "stage            student acc   ECE    halluc",
        f"P0 baseline      {p0['student']['accuracy']:.3f}       {p0['student']['ece']:.3f}  {p0['student']['hallucination_rate']:.3f}",
        f"P1 distill       {p1['student']['accuracy']:.3f}       {p1['student']['ece']:.3f}  {p1['student']['hallucination_rate']:.3f}",
        f"P2 RLCR          {p2['student']['accuracy']:.3f}       {p2['student']['ece']:.3f}  {p2['student']['hallucination_rate']:.3f}",
        f"teacher          {p0['teacher']['accuracy']:.3f}       {p0['teacher']['ece']:.3f}  {p0['teacher']['hallucination_rate']:.3f}",
        "",
        "P3 TRIAGE        accuracy   mean cost   halluc",
        f"teacher only     {p3['teacher_only']['accuracy']:.3f}      {p3['teacher_only']['mean_cost']:.1f}       {p3['teacher_only']['hallucination_rate']:.3f}",
        f"triage           {p3['triage']['accuracy']:.3f}      {p3['triage']['mean_cost']:.1f}       {p3['triage']['hallucination_rate']:.3f}",
        f"recommended without memory: {p3['recommended_policy']}",
        "",
        f"P4 HIKMAT (golden accuracy without memory: {report['p4_hikmat']['golden_accuracy_without_memory']:.3f})",
        "day   accuracy  cost   teacher-only acc/cost   retrieve  escalate  golden  rollback",
    ]
    for d in report["p4_hikmat"]["days"]:
        lines.append(
            f"{d['day']:>3}   {d['accuracy']:.3f}    {d['mean_cost']:5.1f}  "
            f"{d['teacher_only_accuracy']:.3f} / {d['teacher_only_cost']:5.1f}        "
            f"{d['actions'].get('retrieve', 0):.2f}      {d['actions'].get('escalate', 0):.2f}      "
            f"{d['golden_accuracy']:.3f}   {d['rolled_back']}"
        )
    lines.append("")
    lines.append(f"golden tamper detected: {report['golden_tamper_detected']}")
    calls = report["teacher_calls"]
    lines.append(f"teacher calls: {calls['made']} made, {calls['served_from_cache']} served from cache")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(prog="mycelium")
    sub = parser.add_subparsers(dest="command", required=True)
    e2e = sub.add_parser("e2e", help="run the full pipeline (mock student, mock or real teacher)")
    e2e.add_argument("--seed", type=int, default=0)
    e2e.add_argument("--out", help="write the full JSON report here")
    e2e.add_argument("--index", choices=INDEX_KINDS, default="numpy", help="HIKMAT vector index")
    e2e.add_argument("--suite", choices=["synthetic", "real"], default="synthetic",
                     help="synthetic problems, or committed GSM8K + MMLU samples")
    e2e.add_argument("--scenario", choices=["basic", "complex"], default="basic",
                     help="complex: topic drift, overconfidence where weak, a teacher blind spot")
    e2e.add_argument("--teacher-url", help="OpenAI-compatible server for the teacher, e.g. http://localhost:8080")
    e2e.add_argument("--teacher-model", default="teacher", help="model name to send to the teacher server")
    e2e.add_argument("--teacher-cost", type=float, default=16.0, help="teacher cost per loop relative to the student")
    e2e.add_argument(
        "--teacher-api-key-env",
        help="name of the environment variable holding the teacher's API key (the key never goes on the command line)",
    )
    bench = sub.add_parser("bench", help="benchmark HIKMAT vector indexes")
    bench.add_argument("--n", type=int, default=100_000, help="number of stored keys")
    bench.add_argument("--queries", type=int, default=500)
    bench.add_argument("--index", choices=INDEX_KINDS, action="append", help="repeat to pick several (default: all available)")
    sim = sub.add_parser("sim-teacher", help="serve a simulated teacher on an OpenAI-compatible endpoint")
    sim.add_argument("--port", type=int, default=8080)
    sim.add_argument("--accuracy", type=float, default=0.93)
    sim.add_argument("--latency", type=float, default=0.0, help="seconds to wait per request")
    ins = sub.add_parser("insights", help="sweep hint strength and transfer; report what memory adds")
    ins.add_argument("--suite", choices=["synthetic", "real"], default="synthetic")
    ins.add_argument("--scenario", choices=["basic", "complex"], default="basic")
    ins.add_argument("--seed", type=int, default=0)
    ins.add_argument("--gain", type=float, action="append", help="hint_gain values (repeat; default: a grid)")
    ins.add_argument("--transfer", type=float, action="append", help="procedural_transfer values (repeat)")
    ins.add_argument("--out", help="write the rows as JSON here")
    args = parser.parse_args()

    if args.command == "bench":
        print(format_rows(benchmark(args.n, args.queries, kinds=args.index), args.n))
        return
    if args.command == "insights":
        base = E2EConfig(seed=args.seed, suite=args.suite, scenario=args.scenario)
        rows = insights.sweep(
            base,
            gains=tuple(args.gain or insights.DEFAULT_GAINS),
            transfers=tuple(args.transfer or insights.DEFAULT_TRANSFERS),
        )
        print(insights.format_rows(rows))
        if args.out:
            with open(args.out, "w") as f:
                json.dump(rows, f, indent=2)
        return
    if args.command == "sim-teacher":
        server = make_server(port=args.port, config=SimConfig(accuracy=args.accuracy, latency_s=args.latency))
        print(f"simulated teacher on http://127.0.0.1:{args.port}/v1/chat/completions (Ctrl+C to stop)")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.shutdown()
        return

    teacher = None
    if args.teacher_url:
        api_key = None
        if args.teacher_api_key_env:
            api_key = os.environ.get(args.teacher_api_key_env)
            if not api_key:
                parser.error(f"environment variable {args.teacher_api_key_env} is not set")
        teacher = OpenAICompatBackend(
            args.teacher_url, args.teacher_model, cost_per_loop=args.teacher_cost, api_key=api_key
        )
    config = E2EConfig(seed=args.seed, memory_index=args.index, suite=args.suite, scenario=args.scenario)
    report = run_e2e(config, teacher=teacher)
    print(_summary(report))
    if args.out:
        with open(args.out, "w") as f:
            json.dump(report, f, indent=2, default=str)


if __name__ == "__main__":
    main()
