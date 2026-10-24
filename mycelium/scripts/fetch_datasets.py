"""Download full GSM8K and MMLU subjects into the JSONL format of `mycelium/data/samples`.

Run on a machine that can reach Hugging Face (not needed for tests):

    pip install datasets
    python scripts/fetch_datasets.py --out data/full

The output files can be loaded with `mycelium.evals.real.load_gsm8k(path)` and
`load_mmlu([paths])`. Full datasets are not committed; only the small samples are.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SUBJECTS = [
    "high_school_physics", "conceptual_physics", "college_physics",
    "high_school_mathematics", "elementary_mathematics", "college_mathematics",
    "high_school_biology", "college_biology", "high_school_chemistry", "college_chemistry",
    "astronomy", "medical_genetics", "high_school_computer_science", "high_school_statistics",
]


def gsm8k_rows(split: str):
    from datasets import load_dataset

    for i, row in enumerate(load_dataset("openai/gsm8k", "main", split=split)):
        solution, final = row["answer"].split("####")
        steps = solution.count("<<") or len([line for line in solution.splitlines() if line.strip()])
        yield {
            "id": f"gsm8k-{split}-{i}",
            "question": row["question"],
            "answer": re.sub(r",", "", final.strip()),
            "steps": max(1, steps),
        }


def mmlu_rows(subject: str, split: str):
    from datasets import load_dataset

    for i, row in enumerate(load_dataset("cais/mmlu", subject, split=split)):
        yield {
            "id": f"mmlu-{subject}-{i}",
            "subject": subject,
            "question": row["question"],
            "choices": list(row["choices"]),
            "answer": "ABCD"[int(row["answer"])],
        }


def write(path: Path, rows) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    return n


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data/full")
    parser.add_argument("--split", default="test")
    parser.add_argument("--subjects", nargs="*", default=SUBJECTS)
    args = parser.parse_args()
    out = Path(args.out)
    print("gsm8k", write(out / f"gsm8k_{args.split}.jsonl", gsm8k_rows(args.split)))
    for subject in args.subjects:
        print(subject, write(out / f"mmlu_{subject}.jsonl", mmlu_rows(subject, args.split)))


if __name__ == "__main__":
    main()
