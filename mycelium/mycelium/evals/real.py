"""Real questions: committed samples of GSM8K, MMLU and GSM-Symbolic.

`mycelium/data/samples/` holds exact copies of public rows (see ATTRIBUTION.md there):
GSM8K grade-school math word problems, MMLU multiple-choice questions in physics,
mathematics (incl. geometry), biology, chemistry, astronomy, genetics and computer
science, and Apple's GSM-Symbolic: 100 GSM8K questions turned into templates with 50
variants each (new names and numbers, same reasoning). GSM-Symbolic is what lets us
ask whether an insight from one variant helps on another. `scripts/fetch_datasets.py` downloads the full sets on a machine that can
reach Hugging Face.

Real backends use the model's hidden state as the HIKMAT key. The mock pipeline needs
a stand-in, so each problem's features mix its subject's direction with a hashed
bag-of-words vector of its own text: questions in one subject look alike, and two
questions sharing words look a bit more alike.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np

from mycelium.evals.datasets import FEATURE_DIM, family_center, stable_seed
from mycelium.types import MCQ_LETTERS, Problem

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "data" / "samples"
SUBJECT_WEIGHT, TEXT_WEIGHT = 0.92, 0.39

# Rough difficulty by course level, used only by the simulated models.
_LEVEL_DIFFICULTY = {"elementary": 0.25, "conceptual": 0.35, "high_school": 0.5, "college": 0.7}
_SUBJECT_DIFFICULTY = {"astronomy": 0.5, "medical_genetics": 0.55}
_WORD = re.compile(r"[a-z0-9]+")


def text_features(text: str, dim: int = FEATURE_DIM) -> np.ndarray:
    """Signed hashing of word unigrams and bigrams into `dim` dimensions."""
    words = _WORD.findall(text.lower())
    v = np.zeros(dim)
    for token in words + [f"{a}_{b}" for a, b in zip(words, words[1:], strict=False)]:
        h = stable_seed("tok", token)
        v[h % dim] += 1.0 if (h >> 32) & 1 else -1.0
    norm = np.linalg.norm(v)
    return v / norm if norm else v


def real_features(family: str, text: str) -> np.ndarray:
    v = SUBJECT_WEIGHT * family_center(family) + TEXT_WEIGHT * text_features(text)
    return v / np.linalg.norm(v)


def subject_difficulty(subject: str) -> float:
    if subject in _SUBJECT_DIFFICULTY:
        return _SUBJECT_DIFFICULTY[subject]
    for level, value in _LEVEL_DIFFICULTY.items():
        if subject.startswith(level):
            return value
    return 0.5


def format_mcq(question: str, choices: list[str]) -> str:
    options = "\n".join(f"{letter}. {choice}" for letter, choice in zip(MCQ_LETTERS, choices, strict=True))
    return f"{question}\n{options}\nAnswer with the letter of the correct option."


def gsm8k_family(steps: int) -> str:
    if steps <= 3:
        return "math:gsm8k-short"
    if steps <= 5:
        return "math:gsm8k-medium"
    return "math:gsm8k-long"


def _read_jsonl(path: Path) -> list[dict]:
    with path.open() as f:
        return [json.loads(line) for line in f if line.strip()]


def load_gsm8k(path: Path | None = None) -> list[Problem]:
    rows = _read_jsonl(path or SAMPLES_DIR / "gsm8k_test.jsonl")
    problems = []
    for row in rows:
        family = gsm8k_family(int(row["steps"]))
        problems.append(
            Problem(
                id=row["id"],
                domain="math",
                prompt=row["question"],
                answer=str(row["answer"]),
                difficulty=float(np.clip(0.15 + 0.1 * int(row["steps"]), 0.0, 0.95)),
                family=family,
                features=real_features(family, row["question"]),
                # GSM-Symbolic rows carry the template they were generated from; GSM8K rows are unique.
                template=row.get("template", ""),
            )
        )
    return problems


def read_gsm_symbolic_rows(path: Path | None = None) -> list[dict]:
    """Apple's rows as they are, including the reference solution text."""
    return _read_jsonl(path or SAMPLES_DIR / "gsm_symbolic.jsonl")


def load_gsm_symbolic(
    path: Path | None = None, *, templates: int | None = None, per_template: int | None = None
) -> list[Problem]:
    """GSM-Symbolic rows in Apple's original format, read verbatim.

    `templates` keeps the first N template ids and `per_template` the first N variants
    of each, so suites can stay small.
    """
    problems = []
    for row in read_gsm_symbolic_rows(path):
        if (templates is not None and row["id"] >= templates) or (
            per_template is not None and row["instance"] >= per_template
        ):
            continue
        solution, final = row["answer"].split("####")
        # No calculator annotations here, so solution lines stand in for steps.
        steps = max(1, len([line for line in solution.splitlines() if line.strip()]))
        family = gsm8k_family(steps)
        problems.append(
            Problem(
                id=f"gsm-symbolic-{row['id']}-{row['instance']}",
                domain="math",
                prompt=row["question"],
                answer=final.strip().replace(",", ""),
                difficulty=float(np.clip(0.15 + 0.1 * steps, 0.0, 0.95)),
                family=family,
                features=real_features(family, row["question"]),
                template=f"gsm-symbolic-{row['id']}",
            )
        )
    return problems


def load_mmlu(paths: list[Path] | None = None) -> list[Problem]:
    paths = paths or sorted(SAMPLES_DIR.glob("mmlu_*.jsonl"))
    problems = []
    for path in paths:
        for row in _read_jsonl(path):
            family = f"mcq:{row['subject']}"
            problems.append(
                Problem(
                    id=row["id"],
                    domain="mcq",
                    prompt=format_mcq(row["question"], row["choices"]),
                    answer=row["answer"],
                    difficulty=subject_difficulty(row["subject"]),
                    family=family,
                    features=real_features(family, row["question"]),
                    choices=tuple(row["choices"]),
                )
            )
    return problems


# ---- full evaluation sets (spec 002 T006): downloaded by scripts/fetch_datasets.py --evals
# into data/full/ (gitignored); only the loaders and tiny fixtures live in the repo.

DATA_FULL = Path("data/full")
EVAL_SOURCES = ("math500", "humanevalplus", "mbppplus", "simpleqa")


def load_math500(path: Path | None = None) -> list[Problem]:
    problems = []
    for row in _read_jsonl(path or DATA_FULL / "math500.jsonl"):
        family = f"math500:{row['subject']}"
        problems.append(Problem(
            id=f"math500-{row['id']}", domain="math", prompt=row["problem"], answer=row["answer"],
            difficulty=0.2 + 0.15 * (int(row["level"]) - 1), family=family,
            features=real_features(family, row["problem"]),
        ))
    return problems


def load_humanevalplus(path: Path | None = None) -> list[Problem]:
    problems = []
    for row in _read_jsonl(path or DATA_FULL / "humanevalplus.jsonl"):
        prompt = f"Complete this Python function and return the whole function.\n\n```python\n{row['prompt']}```"
        problems.append(Problem(
            id=f"humanevalplus-{row['id']}", domain="code", prompt=prompt,
            # EvalPlus tests define check(candidate); calling it runs every case.
            answer=f"{row['test']}\n\ncheck({row['entry_point']})\n",
            difficulty=0.5, family="code:humanevalplus", features=real_features("code:humanevalplus", row["prompt"]),
        ))
    return problems


def load_mbppplus(path: Path | None = None) -> list[Problem]:
    problems = []
    for row in _read_jsonl(path or DATA_FULL / "mbppplus.jsonl"):
        # The task text doesn't name the function; the first test shows its name and use.
        prompt = f"{row['prompt']}\nYour code must pass this test:\n{row['example']}"
        problems.append(Problem(
            id=f"mbppplus-{row['id']}", domain="code", prompt=prompt, answer=row["test"],
            difficulty=0.45, family="code:mbppplus", features=real_features("code:mbppplus", row["prompt"]),
        ))
    return problems


def load_simpleqa(path: Path | None = None) -> list[Problem]:
    problems = []
    for row in _read_jsonl(path or DATA_FULL / "simpleqa.jsonl"):
        family = "qa:simpleqa"
        problems.append(Problem(
            id=row["id"], domain="qa", prompt=row["question"], answer=row["answer"],
            difficulty=0.9, family=family, features=real_features(family, row["question"]),
        ))
    return problems


def load_eval_source(source: str, data_dir: Path = DATA_FULL) -> list[Problem]:
    loaders = {"math500": load_math500, "humanevalplus": load_humanevalplus,
               "mbppplus": load_mbppplus, "simpleqa": load_simpleqa}
    return loaders[source](data_dir / f"{source}.jsonl")


def load_real() -> list[Problem]:
    """Every committed real sample, in a fixed order."""
    return load_gsm8k() + load_mmlu()


def split(problems: list[Problem], fractions: tuple[float, ...], seed: int = 0) -> list[list[Problem]]:
    """Deterministic shuffle by id, then cut into consecutive parts."""
    order = sorted(problems, key=lambda p: stable_seed("split", seed, p.id))
    cuts = np.cumsum([0, *[round(f * len(order)) for f in fractions]])
    cuts[-1] = len(order)
    return [order[a:b] for a, b in zip(cuts[:-1], cuts[1:], strict=True)]
