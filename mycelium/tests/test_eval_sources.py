"""Full eval sets (spec 002 T006): loaders and judges, on small fixtures, no network."""

import json
from pathlib import Path

import pytest

from mycelium.evals.judges import _normalize_latex, judge, judge_math, judge_short_answer
from mycelium.evals.real import load_humanevalplus, load_math500, load_mbppplus, load_simpleqa
from mycelium.models.openai_compat import system_prompt
from mycelium.types import Answer

FIXTURES = Path(__file__).parent / "fixtures"


def _rows(name):
    return [json.loads(line) for line in (FIXTURES / name).read_text().splitlines()]


@pytest.mark.parametrize("source", ["humanevalplus", "mbppplus"])
def test_reference_solutions_pass_and_stubs_fail(source):
    loader = {"humanevalplus": load_humanevalplus, "mbppplus": load_mbppplus}[source]
    problems, rows = loader(FIXTURES / f"{source}.jsonl"), _rows(f"{source}.jsonl")
    for problem, row in zip(problems, rows, strict=True):
        reference = row["prompt"] + row["canonical_solution"] if source == "humanevalplus" else row["canonical_solution"]
        assert judge(problem, Answer(reference, 0.9, 1))
        assert not judge(problem, Answer("def f():\n    return None", 0.9, 1))


def test_mbpp_prompt_names_the_function_through_its_first_test():
    problem = load_mbppplus(FIXTURES / "mbppplus.jsonl")[0]
    assert _rows("mbppplus.jsonl")[0]["example"] in problem.prompt


def test_math_expressions_are_judged_beyond_numbers():
    problems = load_math500(FIXTURES / "math500.jsonl")
    assert judge(problems[0], Answer(r"\dfrac{5}{6}", 0.9, 1))
    assert judge(problems[1], Answer(r"\boxed{(3, \frac{\pi}{2})}", 0.9, 1))
    assert not judge(problems[1], Answer(r"(3, \pi)", 0.9, 1))
    assert _normalize_latex(r"\left( 3, \frac{\pi}{2} \right)") == r"(3,\frac{\pi}{2})"
    assert judge_math("18", "The answer is 18")  # plain numbers keep the old judge
    assert "LaTeX" in system_prompt("math", problems[0].family) and "LaTeX" not in system_prompt("math")


def test_simpleqa_short_answers():
    problems = load_simpleqa(FIXTURES / "simpleqa.jsonl")
    first = problems[0]
    assert judge(first, Answer(first.answer, 0.9, 1))
    assert judge_short_answer("1995", "In 1995.")
    assert not judge_short_answer("Michio Sugeno", "Sugeno")
    assert not judge_short_answer("Paris", "Paris " + "and many other cities " * 10)  # long hedges don't count
