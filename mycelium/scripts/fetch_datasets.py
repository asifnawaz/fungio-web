"""Download full GSM8K and MMLU subjects into the JSONL format of `mycelium/data/samples`.

Run on a machine that can reach Hugging Face (not needed for tests):

    pip install datasets
    python scripts/fetch_datasets.py --out data/full

The output files can be loaded with `mycelium.evals.real.load_gsm8k(path)` and
`load_mmlu([paths])`. Full datasets are not committed; only the small samples are.

`--gsm-symbolic` also downloads the P1 and P2 variants of apple/GSM-Symbolic (one and
two extra clauses per question) into `data/full/`. The main variant is already committed
as `mycelium/data/samples/gsm_symbolic.jsonl`; see ATTRIBUTION.md there for the license.
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


def gsm_symbolic_rows(config: str = "main"):
    from datasets import load_dataset

    for row in load_dataset("apple/GSM-Symbolic", config, split="test"):
        solution, final = row["answer"].split("####")
        yield {
            "id": f"gsm-symbolic-{config}-{row['id']}-{row['instance']}",
            "question": row["question"],
            "answer": re.sub(r",", "", final.strip()),
            "steps": max(1, solution.count("<<") or len([line for line in solution.splitlines() if line.strip()])),
            "template": f"gsm-symbolic-{config}-{row['id']}",
        }


def _hub_file(repo: str, filename: str) -> str:
    from huggingface_hub import hf_hub_download

    return hf_hub_download(repo, filename, repo_type="dataset")


def eval_rows(source: str):
    """Full evaluation sets for spec 002 T006 (ids and licenses in specs/ROADMAP.md)."""
    if source == "math500":
        for line in open(_hub_file("HuggingFaceH4/MATH-500", "test.jsonl")):
            row = json.loads(line)
            yield {"id": row["unique_id"], "problem": row["problem"], "answer": row["answer"],
                   "subject": row["subject"], "level": row["level"]}
    elif source == "humanevalplus":
        for line in open(_hub_file("evalplus/humanevalplus", "test.jsonl")):
            row = json.loads(line)
            yield {"id": row["task_id"], "prompt": row["prompt"], "entry_point": row["entry_point"],
                   "test": row["test"], "canonical_solution": row["canonical_solution"]}
    elif source == "mbppplus":
        import pyarrow.parquet as pq

        path = _hub_file("evalplus/mbppplus", "data/test-00000-of-00001-d5781c9c51e02795.parquet")
        for row in pq.read_table(path).to_pylist():
            yield {"id": row["task_id"], "prompt": row["prompt"], "example": row["test_list"][0],
                   "test": row["test"], "canonical_solution": row["code"]}
    elif source == "simpleqa":
        import ast
        import csv

        for i, row in enumerate(csv.DictReader(open(_hub_file("basicv8vc/SimpleQA", "simple_qa_test_set.csv")))):
            # metadata is a Python dict literal, not JSON.
            topic = ast.literal_eval(row["metadata"]).get("topic", "") if row["metadata"] else ""
            yield {"id": f"simpleqa-{i}", "question": row["problem"], "answer": row["answer"], "topic": topic}
    else:
        raise ValueError(source)


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
    parser.add_argument("--gsm-symbolic", action="store_true", help="also fetch GSM-Symbolic P1 and P2")
    parser.add_argument("--evals", action="store_true",
                        help="only fetch MATH-500, HumanEval+, MBPP+ and SimpleQA (needs huggingface_hub, pyarrow)")
    args = parser.parse_args()
    out = Path(args.out)
    if args.evals:
        for source in ("math500", "humanevalplus", "mbppplus", "simpleqa"):
            print(source, write(out / f"{source}.jsonl", eval_rows(source)))
        return
    print("gsm8k", write(out / f"gsm8k_{args.split}.jsonl", gsm8k_rows(args.split)))
    for subject in args.subjects:
        print(subject, write(out / f"mmlu_{subject}.jsonl", mmlu_rows(subject, args.split)))
    if args.gsm_symbolic:
        for config in ("p1", "p2"):
            print(f"gsm-symbolic-{config}", write(out / f"gsm_symbolic_{config}.jsonl", gsm_symbolic_rows(config)))


if __name__ == "__main__":
    main()
