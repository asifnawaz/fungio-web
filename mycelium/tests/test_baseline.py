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
