"""The spec 003 kill test must find a hint effect when there is one, report none when
there isn't, and resume a long run without repeating work."""

import pytest

from mycelium import killtest
from mycelium.models.openai_compat import OpenAICompatBackend
from mycelium.pipeline import make_student
from mycelium.sim_teacher import start_in_background


def _mock(gain, transfer=0.25, skill=0.45, seed=0):
    student = make_student(hint_gain=gain, procedural_transfer=transfer)
    student.skill["math"] = skill
    student.seed = seed
    return student


def _measure(student, templates=30, variants=10, fit=True):
    trials = killtest.run(
        student, templates=killtest.choose_templates(templates), variants=variants, payload=killtest.tag_payload
    )
    return killtest.analyze(trials, boot=300, fit=fit)


def test_other_donor_is_a_different_template_of_the_same_family():
    items = killtest.load_items()
    for template in range(killtest.N_TEMPLATES):
        donor = killtest.other_donor(template, items)
        assert donor != template
        assert items[(donor, 0)].problem.family == items[(template, 0)].problem.family


def test_a_real_effect_is_found_and_its_size_recovered():
    report = _measure(_mock(gain=0.4))
    assert report["verdict"] == "pays"
    assert report["ci95"]["d_acc_same"][0] > 0
    low, high = report["mock_equivalents"]["hint_gain_ci95"]
    assert low <= 0.4 <= high
    assert report["mock_equivalents"]["procedural_transfer"] == pytest.approx(0.25, abs=0.25)


@pytest.mark.parametrize("gain", [0.0, -0.2])
def test_no_effect_or_harm_is_a_kill(gain):
    report = _measure(_mock(gain=gain), fit=False)
    assert report["verdict"] == "kill"
    assert report["d_acc_same"] <= 0


@pytest.mark.parametrize(
    ("d_acc", "acc_ci", "d_effort", "effort_ci", "expected"),
    [
        (0.05, (0.01, 0.09), 0.0, (-0.02, 0.02), "pays"),  # more right answers
        (0.0, (-0.01, 0.01), -0.20, (-0.30, -0.10), "pays"),  # same accuracy, 20% fewer tokens
        (0.0, (-0.01, 0.01), -0.01, (-0.03, 0.01), "kill"),  # nothing changes
        (0.03, (-0.02, 0.08), -0.05, (-0.15, 0.04), "inconclusive"),  # too few problems to tell
        (-0.05, (-0.09, -0.01), -0.30, (-0.40, -0.20), "kill"),  # cheaper but wrong more often
    ],
)
def test_preregistered_verdict(d_acc, acc_ci, d_effort, effort_ci, expected):
    point = {"d_acc_same": d_acc, "d_effort_same": d_effort}
    ci = {"d_acc_same": acc_ci, "d_effort_same": effort_ci}
    assert killtest.verdict(point, ci) == expected


def test_a_rerun_resumes_without_asking_the_model_again(tmp_path):
    class Counting:
        def __init__(self, model):
            self.model, self.calls = model, 0

        def answer(self, problem, **kwargs):
            self.calls += 1
            return self.model.answer(problem, **kwargs)

    path = tmp_path / "trials.jsonl"
    first = Counting(_mock(gain=0.4))
    trials = killtest.run(first, templates=[0, 1], variants=3, payload=killtest.tag_payload, trials_path=path)
    assert first.calls == len(trials) == 2 * 3 * 3
    again = Counting(_mock(gain=0.4))
    resumed = killtest.run(again, templates=[0, 1], variants=3, payload=killtest.tag_payload, trials_path=path)
    assert again.calls == 0 and resumed == trials


def test_runs_over_http_against_the_simulated_teacher():
    server, url = start_in_background()
    try:
        backend = OpenAICompatBackend(url, "sim-qwen", tokens_per_loop=2048)
        trials = killtest.run(backend, templates=[0, 1, 2], variants=2, max_loops=1)
    finally:
        server.shutdown()
    assert len(trials) == 3 * 2 * 3
    assert all(t.effort > 1 for t in trials)  # real token counts, not loops
    report = killtest.analyze(trials, boot=100, fit=False)
    assert report["targets"] == 6


def test_report_matches_its_contract():
    import json
    from pathlib import Path

    schema = json.loads(
        (Path(__file__).parent.parent / "specs/003-insight-kill-test/contracts/report.schema.json").read_text()
    )
    report = _measure(_mock(gain=0.4), templates=5, variants=4)
    assert set(schema["required"]) <= set(report)
    assert set(schema["properties"]["ci95"]["required"]) <= set(report["ci95"])
    assert set(schema["properties"]["mock_equivalents"]["required"]) <= set(report["mock_equivalents"])
    assert report["verdict"] in schema["properties"]["verdict"]["enum"]
    json.dumps(report)  # serializable as written by --out


def test_parallel_workers_give_the_same_trials():
    serial = killtest.run(_mock(gain=0.4), templates=[0, 1, 2], variants=3, payload=killtest.tag_payload)
    parallel = killtest.run(_mock(gain=0.4), templates=[0, 1, 2], variants=3, payload=killtest.tag_payload, workers=4)
    assert parallel == serial
