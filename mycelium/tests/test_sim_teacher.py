"""The whole pipeline through a real HTTP teacher (the simulated one)."""

import pytest

from mycelium.evals.datasets import make_suite
from mycelium.evals.harness import evaluate
from mycelium.models.openai_compat import OpenAICompatBackend
from mycelium.pipeline import E2EConfig, run_e2e
from mycelium.sim_teacher import SimConfig, solve, start_in_background


@pytest.fixture(scope="module")
def teacher_url():
    server, url = start_in_background(SimConfig(accuracy=0.93))
    yield url
    server.shutdown()


def test_solver_reads_every_synthetic_prompt():
    for problem in make_suite(41, 30):
        domain, right, _ = solve(problem.prompt)
        assert domain == problem.domain
        if problem.domain == "code":
            continue  # judged by running tests below
        assert right == problem.answer


def test_teacher_over_http_is_accurate_and_honest(teacher_url):
    # Identical prompts get identical answers at temperature 0 (as with a real model), so
    # one code family is right or wrong as a block; a larger suite keeps the check stable.
    teacher = OpenAICompatBackend(teacher_url, "sim-qwen", cost_per_loop=16)
    report = evaluate(lambda p: teacher.answer(p, max_loops=8), make_suite(42, 60))
    assert report["accuracy"] > 0.8
    assert report["abstain_rate"] > 0  # unknown entities are declined, not invented
    assert report["hallucination_rate"] < 0.2


def test_full_pipeline_runs_through_http_teacher(teacher_url):
    small = E2EConfig(train_per_domain=60, eval_per_domain=30, rlcr_steps=3, days=3, day_per_domain=20, poison_day=1)
    report = run_e2e(small, teacher=OpenAICompatBackend(teacher_url, "sim-qwen", cost_per_loop=16))
    assert report["p0_baseline"]["teacher"]["accuracy"] > report["p0_baseline"]["student"]["accuracy"]
    assert report["p1_distill"]["student"]["accuracy"] > report["p0_baseline"]["student"]["accuracy"]
    assert report["teacher_calls"]["served_from_cache"] > 0
    assert report["golden_tamper_detected"]
    hikmat = report["p4_hikmat"]
    assert hikmat["days"][small.poison_day]["rolled_back"]
