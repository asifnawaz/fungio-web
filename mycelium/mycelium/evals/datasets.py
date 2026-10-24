"""Synthetic problem suites for end-to-end testing without real models or datasets.

Problems come in families (same skill, different numbers or entities). Each family has
a stable feature direction, so problems from one family look alike to HIKMAT the way
real problems of one type produce similar hidden states.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np

from mycelium.types import Problem

FEATURE_DIM = 64
FEATURE_NOISE = 0.3


def stable_seed(*parts) -> int:
    digest = hashlib.sha256("|".join(map(str, parts)).encode()).digest()
    return int.from_bytes(digest[:8], "little")


def family_center(family: str) -> np.ndarray:
    v = np.random.default_rng(stable_seed("family", family)).normal(size=FEATURE_DIM)
    return v / np.linalg.norm(v)


def problem_features(family: str, rng: np.random.Generator) -> np.ndarray:
    noise = rng.normal(scale=FEATURE_NOISE / np.sqrt(FEATURE_DIM), size=FEATURE_DIM)
    v = family_center(family) + noise
    return v / np.linalg.norm(v)


# ---- math -------------------------------------------------------------------

MATH_FAMILIES = {
    "add_small": 0.20,
    "sub_medium": 0.35,
    "mod": 0.50,
    "mul_small": 0.50,
    "mul_medium": 0.65,
    "chain": 0.75,
}


def _math_problem(family: str, rng: np.random.Generator) -> tuple[str, int]:
    if family == "add_small":
        a, b = rng.integers(10, 100, size=2)
        return f"What is {a} + {b}?", int(a + b)
    if family == "sub_medium":
        a, b = rng.integers(100, 1000, size=2)
        return f"What is {a} - {b}?", int(a - b)
    if family == "mod":
        a, b = int(rng.integers(100, 1000)), int(rng.integers(3, 20))
        return f"What is {a} mod {b}?", a % b
    if family == "mul_small":
        a, b = rng.integers(2, 31, size=2)
        return f"What is {a} * {b}?", int(a * b)
    if family == "mul_medium":
        a, b = rng.integers(10, 100, size=2)
        return f"What is {a} * {b}?", int(a * b)
    if family == "chain":
        a, b, c = rng.integers(2, 50, size=3)
        return f"What is {a} + {b} * {c}?", int(a + b * c)
    raise ValueError(family)


# ---- code -------------------------------------------------------------------


@dataclass(frozen=True)
class CodeTask:
    difficulty: float
    signature: str
    solution: str
    buggy: str

    def tests(self, rng: np.random.Generator) -> str:
        return _CODE_TESTS[self.signature.split("(")[0]](rng)


CODE_TASKS = {
    "add": CodeTask(0.20, "add(a, b)", "def add(a, b):\n    return a + b", "def add(a, b):\n    return a - b"),
    "reverse": CodeTask(0.25, "reverse(s)", "def reverse(s):\n    return s[::-1]", "def reverse(s):\n    return s"),
    "is_even": CodeTask(0.30, "is_even(n)", "def is_even(n):\n    return n % 2 == 0", "def is_even(n):\n    return n % 2 == 1"),
    "max_list": CodeTask(0.40, "max_list(xs)", "def max_list(xs):\n    return max(xs)", "def max_list(xs):\n    return xs[0]"),
    "count_vowels": CodeTask(
        0.50,
        "count_vowels(s)",
        "def count_vowels(s):\n    return sum(c in 'aeiou' for c in s.lower())",
        "def count_vowels(s):\n    return s.count('a')",
    ),
    "factorial": CodeTask(
        0.60,
        "factorial(n)",
        "def factorial(n):\n    out = 1\n    for i in range(2, n + 1):\n        out *= i\n    return out",
        "def factorial(n):\n    out = 1\n    for i in range(2, n):\n        out *= i\n    return out",
    ),
    "fizzbuzz": CodeTask(
        0.70,
        "fizzbuzz(n)",
        "def fizzbuzz(n):\n    if n % 15 == 0:\n        return 'FizzBuzz'\n    if n % 3 == 0:\n        return 'Fizz'\n"
        "    if n % 5 == 0:\n        return 'Buzz'\n    return str(n)",
        "def fizzbuzz(n):\n    if n % 3 == 0:\n        return 'Fizz'\n    if n % 5 == 0:\n        return 'Buzz'\n    return str(n)",
    ),
}


def _tests_add(rng):
    a, b = rng.integers(-50, 50, size=2)
    return f"assert add({a}, {b}) == {a + b}\nassert add(0, 0) == 0"


def _tests_reverse(rng):
    word = "".join(rng.choice(list("abcdefgh"), size=int(rng.integers(3, 8))))
    return f"assert reverse({word!r}) == {word[::-1]!r}\nassert reverse('ab') == 'ba'"


def _tests_is_even(rng):
    n = int(rng.integers(0, 100))
    return f"assert is_even({n}) == {n % 2 == 0}\nassert is_even(3) is False"


def _tests_max_list(rng):
    xs = [int(x) for x in rng.integers(-20, 20, size=5)]
    return f"assert max_list({xs}) == {max(xs)}\nassert max_list([1, 9, 3]) == 9"


def _tests_count_vowels(rng):
    word = "".join(rng.choice(list("abeioudfg"), size=8))
    return f"assert count_vowels({word!r}) == {sum(c in 'aeiou' for c in word)}\nassert count_vowels('queue') == 4"


def _tests_factorial(rng):
    n = int(rng.integers(3, 9))
    value = 1
    for i in range(2, n + 1):
        value *= i
    return f"assert factorial({n}) == {value}\nassert factorial(1) == 1"


def _tests_fizzbuzz(rng):
    n = int(rng.integers(1, 100))
    want = "FizzBuzz" if n % 15 == 0 else "Fizz" if n % 3 == 0 else "Buzz" if n % 5 == 0 else str(n)
    return f"assert fizzbuzz({n}) == {want!r}\nassert fizzbuzz(30) == 'FizzBuzz'"


_CODE_TESTS = {
    "add": _tests_add,
    "reverse": _tests_reverse,
    "is_even": _tests_is_even,
    "max_list": _tests_max_list,
    "count_vowels": _tests_count_vowels,
    "factorial": _tests_factorial,
    "fizzbuzz": _tests_fizzbuzz,
}

# ---- qa ---------------------------------------------------------------------

QA_RELATIONS = {"capital": 0.30, "river": 0.45, "founder": 0.60, "anthem": 0.75}
UNANSWERABLE_SHARE = 0.2
_SYLLABLES = ["zor", "vex", "mi", "rel", "da", "ka", "lun", "tor", "ia", "sen", "qua", "bo"]


def fake_name(rng: np.random.Generator, parts: int = 3) -> str:
    return "".join(rng.choice(_SYLLABLES, size=parts)).capitalize()


def qa_world(seed: int = 7, entities_per_relation: int = 40) -> dict[tuple[str, str], str]:
    """A fixed synthetic world of facts, shared by every split."""
    rng = np.random.default_rng(seed)
    return {
        (relation, fake_name(rng)): fake_name(rng, 2)
        for relation in QA_RELATIONS
        for _ in range(entities_per_relation)
    }


# ---- suites -----------------------------------------------------------------


def make_suite(seed: int, per_domain: int, families: dict[str, list[str]] | None = None) -> list[Problem]:
    """Build a mixed suite. `families` optionally restricts which families each domain uses."""
    rng = np.random.default_rng(seed)
    world = qa_world()
    world_keys = list(world)
    problems: list[Problem] = []

    def pick(domain: str, options: list[str]) -> str:
        allowed = families.get(domain, options) if families else options
        return str(rng.choice(allowed))

    for i in range(per_domain):
        family = pick("math", list(MATH_FAMILIES))
        prompt, value = _math_problem(family, rng)
        problems.append(
            Problem(
                id=f"s{seed}-math-{i}",
                domain="math",
                prompt=prompt,
                answer=str(value),
                difficulty=float(np.clip(MATH_FAMILIES[family] + rng.normal(0, 0.05), 0, 1)),
                family=f"math:{family}",
                template=f"math:{family}",  # same procedure, new numbers
                features=problem_features(f"math:{family}", rng),
            )
        )

    for i in range(per_domain):
        family = pick("code", list(CODE_TASKS))
        task = CODE_TASKS[family]
        problems.append(
            Problem(
                id=f"s{seed}-code-{i}",
                domain="code",
                prompt=f"Write a Python function {task.signature}.",
                answer=task.tests(rng),
                difficulty=float(np.clip(task.difficulty + rng.normal(0, 0.05), 0, 1)),
                family=f"code:{family}",
                template=f"code:{family}",  # same function, new test values
                features=problem_features(f"code:{family}", rng),
            )
        )

    for i in range(per_domain):
        relation = pick("qa", list(QA_RELATIONS))
        if rng.random() < UNANSWERABLE_SHARE:
            entity, answer = fake_name(rng, 4), None  # not in the world: nobody can know this
        else:
            candidates = [k for k in world_keys if k[0] == relation]
            key = candidates[int(rng.integers(len(candidates)))]
            entity, answer = key[1], world[key]
        problems.append(
            Problem(
                id=f"s{seed}-qa-{i}",
                domain="qa",
                prompt=f"What is the {relation} of {entity}?",
                answer=answer,
                difficulty=float(np.clip(QA_RELATIONS[relation] + rng.normal(0, 0.05), 0, 1)),
                family=f"qa:{relation}",
                features=problem_features(f"qa:{relation}", rng),
            )
        )
    return problems
