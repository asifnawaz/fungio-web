"""P0 on real hardware: one model, measured alone, through the same HTTP client."""

from mycelium.baseline import format_baseline, run_baseline
from mycelium.models.openai_compat import OpenAICompatBackend
from mycelium.pipeline import E2EConfig, build_real_suite
from mycelium.sim_teacher import start_in_background


def test_baseline_over_http_reports_per_domain_and_speed():
    server, url = start_in_background()
    try:
        report = run_baseline(OpenAICompatBackend(url, "sim-qwen", tokens_per_loop=2048), E2EConfig(suite="real"))
    finally:
        server.shutdown()
    suite = build_real_suite(E2EConfig(suite="real"))
    assert report["overall"]["n"] == len(suite.tune) + len(suite.test)  # holdout only, never golden
    assert set(report["by_domain"]) == {"math", "mcq", "qa"}  # qa = the fictional unanswerables
    assert report["tokens"] > 0 and report["tokens_per_second"] > 0
    assert 0 <= report["default_confidence_share"] <= 1
    assert "tokens/s" in format_baseline(report)


def _report(model: str, suite: str, n: int, acc: float) -> dict:
    overall = {"n": n, "accuracy": acc, "ece": 0.1, "hallucination_rate": 1 - acc}
    return {"model": model, "suite": suite, "overall": overall, "tokens_per_second": 40.0}


def test_compare_puts_models_side_by_side_and_flags_different_question_sets():
    from mycelium.baseline import compare_reports

    table = compare_reports([
        _report("qwen3.5-2b", "real", 111, 0.577), _report("lfm3-1.7b", "real", 111, 0.640),
        _report("qwen3.5-2b", "math500", 100, 0.590), _report("lfm3-1.7b", "math500", 500, 0.700),
        _report("qwen3.5-2b", "simpleqa", 100, 0.010),
    ]).splitlines()
    assert "qwen3.5-2b" in table[0] and table[0].index("qwen3.5-2b") < table[0].index("lfm3-1.7b")
    real, math500, simpleqa = table[2:]
    assert real.startswith("| real | 111 |") and "0.577" in real and "0.640" in real
    assert "differs: 100/500" in math500  # other --limit: not comparable, must not look comparable
    assert simpleqa.endswith("not run |")
