"""Real GSM8K + MMLU samples: loading, multiple-choice judging, and the full pipeline on them."""

import numpy as np
import pytest

from mycelium.evals.judges import judge, mcq_letter
from mycelium.evals.real import format_mcq, load_gsm8k, load_mmlu, load_real, split
from mycelium.pipeline import E2EConfig, run_e2e
from mycelium.sim_teacher import solve
from mycelium.types import Answer


def test_samples_load_with_expected_shape():
    gsm8k, mmlu = load_gsm8k(), load_mmlu()
    assert len(gsm8k) == 80 and len(mmlu) == 250
    assert gsm8k[0].answer == "18"  # GSM8K test row 0: Janet's ducks
    assert all(len(p.choices) == 4 and p.answer in "ABCD" for p in mmlu)
    subjects = {p.family for p in mmlu}
    assert {"mcq:high_school_physics", "mcq:high_school_biology", "mcq:high_school_chemistry",
            "mcq:high_school_mathematics", "mcq:astronomy"} <= subjects
    assert len({p.id for p in gsm8k + mmlu}) == 330


def test_same_subject_questions_look_alike():
    mmlu = load_mmlu()
    physics = [p.features for p in mmlu if p.family == "mcq:high_school_physics"]
    biology = [p.features for p in mmlu if p.family == "mcq:high_school_biology"]
    within = np.mean([a @ b for a, b in zip(physics, physics[1:], strict=False)])
    across = np.mean([a @ b for a, b in zip(physics, biology, strict=False)])
    assert within > 0.75 > across


@pytest.mark.parametrize(
    "reply,letter",
    [("B", "B"), ("(C)", "C"), ("D. 9.8 m/s^2", "D"), ("The answer is A", "A"),
     ("I think it is C because ...", "C"), ("A planet orbits the sun.", None), ("no idea", None)],
)
def test_mcq_letter_parsing(reply, letter):
    assert mcq_letter(reply) == letter


def test_mcq_judging():
    problem = load_mmlu()[0]
    assert judge(problem, Answer(problem.answer, 0.9, 1))
    wrong = next(c for c in "ABCD" if c != problem.answer)
    assert not judge(problem, Answer(wrong, 0.9, 1))


def test_prompt_format_and_split():
    assert format_mcq("Q?", ["w", "x", "y", "z"]).splitlines() == [
        "Q?", "A. w", "B. x", "C. y", "D. z", "Answer with the letter of the correct option."]
    parts = split(load_real(), (0.5, 0.3, 0.2), seed=0)
    ids = [{p.id for p in part} for part in parts]
    assert sum(map(len, ids)) == 330 and not (ids[0] & ids[1] or ids[0] & ids[2] or ids[1] & ids[2])
    assert [p.id for p in split(load_real(), (0.5, 0.3, 0.2), seed=0)[0]] == [p.id for p in parts[0]]


def test_simulated_teacher_knows_the_real_answers():
    for problem in load_real():
        domain, right, _ = solve(problem.prompt)
        assert (domain, right) == (problem.domain, problem.answer)


@pytest.fixture(scope="module")
def complex_report():
    return run_e2e(E2EConfig(suite="real", scenario="complex"))


def test_real_complex_scenario_end_to_end(complex_report):
    r = complex_report
    assert r["suite"]["sizes"]["golden"] > 50
    assert r["p1_distill"]["student"]["accuracy"] > r["p0_baseline"]["student"]["accuracy"]
    # RLCR removes the extra overconfidence on weak subjects.
    assert r["p2_rlcr"]["student"]["ece"] < 0.5 * r["p1_distill"]["student"]["ece"]
    later = r["p4_hikmat"]["days"][1:]
    assert np.mean([d["mean_cost"] for d in later]) < np.mean([d["teacher_only_cost"] for d in later])


def test_real_complex_scenario_safety_gates(complex_report):
    hikmat = complex_report["p4_hikmat"]
    poison_day = hikmat["days"][complex_report["config"]["poison_day"]]
    reviews = {e["record"]: e["decision"] for e in hikmat["events"] if e["type"] == "review"}
    assert reviews[poison_day["attacks"]["quarantined_poison"]] == "rejected"
    assert poison_day["rolled_back"]
    assert complex_report["golden_tamper_detected"]
