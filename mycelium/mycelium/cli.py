"""Command line entry: `python -m mycelium.cli e2e --out report.json`."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from mycelium import baseline, doctor, insights, killtest, rsi
from mycelium.bench import benchmark, format_rows
from mycelium.models.openai_compat import OpenAICompatBackend
from mycelium.pipeline import E2EConfig, run_e2e
from mycelium.sim_teacher import SimConfig, make_server

INDEX_KINDS = ["numpy", "binary-ivf", "faiss-hnsw"]
SUITES = ["synthetic", "real", "symbolic"]


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
    e2e.add_argument("--suite", choices=SUITES, default="synthetic",
                     help="synthetic problems, committed GSM8K + MMLU samples, or GSM-Symbolic + MMLU")
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
    ins.add_argument("--suite", choices=SUITES, default="synthetic")
    ins.add_argument("--scenario", choices=["basic", "complex"], default="basic")
    ins.add_argument("--seed", type=int, default=0)
    ins.add_argument("--gain", type=float, action="append", help="hint_gain values (repeat; default: a grid)")
    ins.add_argument("--transfer", type=float, action="append", help="procedural_transfer values (repeat)")
    ins.add_argument("--out", help="write the rows as JSON here")
    kt = sub.add_parser("killtest", help="spec 003: does a stored verified method help a model on GSM-Symbolic?")
    kt_backend = kt.add_mutually_exclusive_group(required=True)
    kt_backend.add_argument("--url", help="OpenAI-compatible server of the model under test")
    kt_backend.add_argument("--mock", action="store_true", help="the mock student (checks the harness, not a model)")
    kt.add_argument("--model", default="student", help="model name to send to the server")
    kt.add_argument("--api-key-env", help="environment variable holding the server's API key")
    kt.add_argument("--templates", type=int, default=50, help="GSM-Symbolic templates to sample (max 100)")
    kt.add_argument("--variants", type=int, default=10, help="target variants per template (max 49)")
    kt.add_argument("--max-tokens", type=int, default=2048)
    kt.add_argument("--seed", type=int, default=0)
    kt.add_argument("--trials", help="append trials here as JSON lines; a rerun resumes from it")
    kt.add_argument("--workers", type=int, default=1, help="requests in flight at once (match llama-server -np)")
    kt.add_argument("--out", help="write the analysis as JSON here")
    base = sub.add_parser("baseline", help="P0 on real hardware: measure one model alone on a real suite's holdout")
    base.add_argument("--url", required=True, help="OpenAI-compatible server of the model to measure")
    base.add_argument("--model", default="student", help="model name to send to the server")
    base.add_argument("--api-key-env", help="environment variable holding the server's API key")
    base.add_argument("--suite", choices=["real", "symbolic", "math500", "humanevalplus", "mbppplus", "simpleqa"],
                      default="real", help="real/symbolic: committed samples' holdout; others: full sets in --data-dir")
    base.add_argument("--data-dir", default="data/full", help="where scripts/fetch_datasets.py --evals wrote the sets")
    base.add_argument("--limit", type=int, help="evaluate a seeded random subset of this size (full sets only)")
    base.add_argument("--max-tokens", type=int, default=2048)
    base.add_argument("--seed", type=int, default=0)
    base.add_argument("--workers", type=int, default=1, help="requests in flight at once (match llama-server -np)")
    base.add_argument("--out", help="write the report as JSON here")
    rs = sub.add_parser("rsi", help="recursive self-improvement loop on the mock student (spec 006)")
    rs.add_argument("--generations", type=int, default=8)
    rs.add_argument("--verify", choices=["judge", "off", "inverted"], default="judge",
                    help="judge: keep verified traces; off/inverted: broken-verifier tests")
    rs.add_argument("--seed", type=int, default=0)
    rs.add_argument("--out", help="write the report as JSON here")
    doc = sub.add_parser("doctor", help="what this machine can run ([CPU] / [GPU] roadmap tasks)")
    doc.add_argument("--network", action="store_true", help="also check that huggingface.co is reachable")
    args = parser.parse_args()

    if args.command == "bench":
        print(format_rows(benchmark(args.n, args.queries, kinds=args.index), args.n))
        return
    if args.command == "baseline":
        api_key = os.environ.get(args.api_key_env) if args.api_key_env else None
        if args.api_key_env and not api_key:
            parser.error(f"environment variable {args.api_key_env} is not set")
        backend = OpenAICompatBackend(args.url, args.model, tokens_per_loop=args.max_tokens, api_key=api_key)
        if args.suite in ("real", "symbolic"):
            report = baseline.run_baseline(backend, E2EConfig(seed=args.seed, suite=args.suite), workers=args.workers)
        else:
            from mycelium.evals.real import load_eval_source, split

            problems = load_eval_source(args.suite, Path(args.data_dir))
            if args.limit:
                problems = split(problems, (1.0,), seed=args.seed)[0][: args.limit]
            report = baseline.evaluate_problems(backend, problems, label=args.suite, workers=args.workers)
        print(baseline.format_baseline(report))
        if args.out:
            _write_json(args.out, report)
        return
    if args.command == "rsi":
        report = rsi.run_rsi(rsi.RSIConfig(generations=args.generations, verify=args.verify, seed=args.seed))
        print(rsi.format_rsi(report))
        if args.out:
            _write_json(args.out, report)
        return
    if args.command == "doctor":
        report = doctor.check(network=args.network)
        print(json.dumps(report, indent=2))
        print("\n".join(doctor.advice(report)))
        return
    if args.command == "killtest":
        _killtest(args, parser)
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
            _write_json(args.out, rows)
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
        _write_json(args.out, report)


def _ensure_parent(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _write_json(path: str, data) -> None:
    """Write a report, creating its folder (e.g. `reports/`) if needed."""
    with open(_ensure_parent(Path(path)), "w") as f:
        json.dump(data, f, indent=2, default=str)


def _killtest(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if not 1 <= args.templates <= killtest.N_TEMPLATES or not 1 <= args.variants <= 49:
        parser.error("--templates must be 1-100 and --variants 1-49")
    if args.mock:
        from mycelium.pipeline import make_student

        backend, payload, unit = make_student(), killtest.tag_payload, "loops"
    else:
        api_key = os.environ.get(args.api_key_env) if args.api_key_env else None
        if args.api_key_env and not api_key:
            parser.error(f"environment variable {args.api_key_env} is not set")
        backend = OpenAICompatBackend(args.url, args.model, tokens_per_loop=args.max_tokens, api_key=api_key)
        payload, unit = killtest.solution_payload, "tokens"
    total = args.templates * args.variants * len(killtest.CONDITIONS)
    count = 0

    def progress(_trial) -> None:
        nonlocal count
        count += 1
        if count % 50 == 0 or count == total:
            print(f"  {count}/{total} trials", flush=True)

    trials = killtest.run(
        backend,
        templates=killtest.choose_templates(args.templates, args.seed),
        variants=args.variants,
        payload=payload,
        # One "loop" = max_tokens for the HTTP backend, so max_loops=1 caps the reply length.
        max_loops=8 if args.mock else 1,
        seed=args.seed,
        trials_path=_ensure_parent(Path(args.trials)) if args.trials else None,
        on_trial=progress,
        workers=1 if args.mock else args.workers,
    )
    report = killtest.analyze(trials, seed=args.seed)
    print(killtest.format_report(report, unit))
    if args.out:
        _write_json(args.out, report)


if __name__ == "__main__":
    main()
