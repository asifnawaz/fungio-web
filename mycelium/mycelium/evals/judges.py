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
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


def judge_math(expected: str, text: str) -> bool:
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


@functools.lru_cache(maxsize=8192)
def judge_code(tests: str, code: str) -> bool:
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
                timeout=CODE_TIMEOUT_S,
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
        return judge_code(problem.answer, answer.text)
    if problem.domain == "qa":
        return judge_qa(problem.answer, answer.text)
    raise ValueError(f"unknown domain {problem.domain!r}")
