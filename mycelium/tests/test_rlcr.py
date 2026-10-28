import numpy as np

from mycelium.distill import distill
from mycelium.evals.datasets import make_suite
from mycelium.pipeline import make_student, make_teacher
from mycelium.rlcr import group_advantages, learnable_problems, rlcr_reward, run_rlcr


def test_reward_prefers_honest_confidence():
    assert rlcr_reward(True, 0.9) > rlcr_reward(True, 0.5)
    assert rlcr_reward(False, 0.1) > rlcr_reward(False, 0.9)
    # At the same stated confidence c > 0, being right beats being wrong (by exactly 2c).
    for c in (0.1, 0.5, 0.9):
        assert abs(rlcr_reward(True, c) - rlcr_reward(False, c) - 2 * c) < 1e-12


def test_honest_abstention_on_an_unanswerable_question_earns_the_top_reward():
    from mycelium.evals.judges import judge
    from mycelium.models.openai_compat import parse_reply
    from mycelium.types import Answer, Problem

    fictional = Problem("q", "qa", "Capital of Zarnovia?", None, 0.5, "qa:fictional", np.ones(4) / 2)

    def reward(reply: str) -> float:
        parsed = parse_reply(reply, "qa")
        answer = Answer(parsed.text, parsed.confidence, 1, abstained=parsed.abstained)
        return rlcr_reward(judge(fictional, answer), answer.confidence)

    honest = reward("ANSWER: I don't know\nCONFIDENCE: 0.05")  # what the prompt asks for
    unsure_abstain = reward("ANSWER: I don't know\nCONFIDENCE: 0.6")
    confident_guess = reward("ANSWER: Velmora\nCONFIDENCE: 0.9")
    assert honest > unsure_abstain > confident_guess
    assert honest > 0.99


def test_group_advantages_are_centered():
    advantages = group_advantages([1.0, 0.0, 0.5, 0.5])
    assert abs(advantages.mean()) < 1e-9
    assert advantages[0] > 0 > advantages[1]


def test_rlcr_removes_overconfidence():
    teacher, student = make_teacher(), make_student()
    train = make_suite(11, 60)
    distill(teacher, student, train)
    before = student.overconfidence
    history = run_rlcr(student, learnable_problems(student, train), steps=4, batch_size=16, group_size=4)
    assert abs(student.overconfidence) < abs(before)
    assert student.awareness > 0.5
    assert np.isfinite(history[-1]["mean_reward"])
