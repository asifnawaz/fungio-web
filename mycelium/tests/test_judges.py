import numpy as np

from mycelium.evals import judges
from mycelium.evals.judges import judge, judge_code, judge_math, judge_qa
from mycelium.types import Answer, Problem


def _problem(domain, answer):
    return Problem("p", domain, "q", answer, 0.5, f"{domain}:x", np.ones(4) / 2)


def test_math_takes_last_number():
    assert judge_math("42", "The answer is 42")
    assert judge_math("2.5", "2.50")
    assert not judge_math("42", "41")
    assert not judge_math("42", "no number here")


def test_qa_ignores_case_punctuation_articles():
    assert judge_qa("Mirelda", "the mirelda.")
    assert not judge_qa("Mirelda", "Mireldo")


def test_code_runs_tests():
    tests = "assert add(2, 3) == 5"
    assert judge_code(tests, "def add(a, b):\n    return a + b")
    assert not judge_code(tests, "def add(a, b):\n    return a - b")
    assert not judge_code(tests, "def add(a, b) return")


def test_code_timeout(monkeypatch):
    monkeypatch.setattr(judges, "CODE_TIMEOUT_S", 1.0)
    assert not judge_code("assert f() == 1", "def f():\n    while True:\n        pass")


def test_unanswerable_rewards_abstaining_only():
    problem = _problem("qa", None)
    assert judge(problem, Answer("", 0.9, 1, abstained=True))
    assert not judge(problem, Answer("Zorvex", 0.9, 1))


def test_abstaining_on_answerable_is_wrong():
    assert not judge(_problem("math", "7"), Answer("", 0.9, 1, abstained=True))
