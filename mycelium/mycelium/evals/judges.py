"""JUDGE: deterministic verifiers. The model under test never grades itself."""

from __future__ import annotations

import functools
import os
import re
import string
import subprocess
import sys
import tempfile

from mycelium.types import Answer, Problem

CODE_TIMEOUT_S = 5.0
# EvalPlus suites run hundreds of extra cases per task; 5 s failed a correct reference
# solution on a busy 4-core machine.
EVALPLUS_TIMEOUT_S = 30.0
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


_NUMERIC = re.compile(r"^-?\d+(?:\.\d+)?$")


def _last_boxed(text: str) -> str:
    """Content of the last \\boxed{...} (brace-balanced), or the text itself."""
    start = text.rfind("\\boxed{")
    if start < 0:
        return text
    depth, i = 0, start + len("\\boxed{") - 1
    for j in range(i, len(text)):
        depth += {"{": 1, "}": -1}.get(text[j], 0)
        if depth == 0:
            return text[i + 1 : j]
    return text


def _normalize_latex(text: str) -> str:
    text = _last_boxed(text).strip().strip("$").strip()
    for old, new in (("\\left", ""), ("\\right", ""), ("\\dfrac", "\\frac"), ("\\tfrac", "\\frac"),
                     ("\\!", ""), ("\\,", ""), ("^{\\circ}", ""), ("^\\circ", ""), ("\\%", ""), ("%", "")):
        text = text.replace(old, new)
    text = re.sub(r"\\text\{([^}]*)\}", r"\1", text)
    return re.sub(r"\s+", "", text).rstrip(".")


def judge_math_expression(expected: str, text: str) -> bool:
    """MATH-style answers (fractions, roots, tuples, intervals in LaTeX).

    Uses the `math-verify` package when installed (symbolic equivalence); otherwise
    compares normalized LaTeX strings, which misses some equivalent forms.
    """
    try:
        from math_verify import parse, verify

        gold, guess = parse(f"${expected}$"), parse(text if "\\boxed" in text else f"${text}$")
        if gold and guess and verify(gold, guess):
            return True
    except ImportError:
        pass
    return _normalize_latex(expected) == _normalize_latex(text)


def judge_math(expected: str, text: str) -> bool:
    if not _NUMERIC.match(expected.strip()):
        return judge_math_expression(expected, text)
    found = _NUMBER.findall(text)
    if not found:
        return False
    got, want = float(found[-1]), float(expected)
    return abs(got - want) <= 1e-6 * max(1.0, abs(want))


def _normalize(text: str) -> str:
    text = text.lower().translate(str.maketrans("", "", string.punctuation))
    words = [w for w in text.split() if w not in {"a", "an", "the"}]
    return " ".join(words)


def judge_qa(expected: str, text: str) -> bool:
    return _normalize(expected) == _normalize(text)


def judge_short_answer(expected: str, text: str) -> bool:
    """SimpleQA-style facts: right if the normalized reference appears in a short reply.

    SimpleQA's own grader is a model; this deterministic check is stricter on paraphrases
    ("Mike" for "Michael") and lenient on extra words, so report it as approximate.
    """
    want, got = _normalize(expected), _normalize(text)
    return bool(want) and len(got) <= 3 * len(want) + 20 and f" {want} " in f" {got} "


# A letter followed by "." ")" ":" or nothing. Not a space: "A planet ..." is not option A.
_LEADING_LETTER = re.compile(r"^\(?([A-D])\)?(?:[.):]|$)")
_ANSWER_IS = re.compile(r"answer\s*(?:is)?\s*[:\-]?\s*\(?([A-D])\)?\b", re.IGNORECASE)
# "A" followed by a lowercase word is the article ("A planet ..."), not option A.
_LONE_LETTER = re.compile(r"\b(A(?!\s+[a-z])|[B-D])\b")


def mcq_letter(text: str) -> str | None:
    """The option letter a reply commits to: a leading letter, "answer is X", or the
    last standalone A-D. None when the reply names no option."""
    text = text.strip()
    for pattern in (_LEADING_LETTER, _ANSWER_IS):
        match = pattern.search(text)
        if match:
            return match.group(1).upper()
    letters = _LONE_LETTER.findall(text)
    return letters[-1] if letters else None


def judge_mcq(expected: str, text: str) -> bool:
    return mcq_letter(text) == expected


@functools.lru_cache(maxsize=8192)
def judge_code(tests: str, code: str, timeout: float = CODE_TIMEOUT_S) -> bool:
    """Run candidate code plus its tests in a separate, isolated interpreter.

    This is process isolation only. Real deployments must run model code in a proper
    sandbox (container, no network, resource limits). Results are cached because the
    same (code, tests) pair always gives the same verdict.
    """
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "candidate.py")
        with open(path, "w") as f:
            f.write(code + "\n\n" + tests + "\n")
        try:
            result = subprocess.run(
                [sys.executable, "-I", path],
                cwd=tmp,
                capture_output=True,
                timeout=timeout,
                env={"PATH": os.environ.get("PATH", "")},
            )
        except subprocess.TimeoutExpired:
            return False
    return result.returncode == 0


def judge(problem: Problem, answer: Answer) -> bool:
    """True when the answer is right. For unanswerable problems, abstaining is right."""
    if not problem.answerable:
        return answer.abstained
    if answer.abstained:
        return False
    if problem.domain == "math":
        return judge_math(problem.answer, answer.text)
    if problem.domain == "code":
        heavy = problem.family in ("code:humanevalplus", "code:mbppplus")
        return judge_code(problem.answer, answer.text, EVALPLUS_TIMEOUT_S if heavy else CODE_TIMEOUT_S)
    if problem.domain == "qa":
        if problem.family.startswith("qa:simpleqa"):
            return judge_short_answer(problem.answer, answer.text)
        return judge_qa(problem.answer, answer.text)
    if problem.domain == "mcq":
        return judge_mcq(problem.answer, answer.text)
    raise ValueError(f"unknown domain {problem.domain!r}")
