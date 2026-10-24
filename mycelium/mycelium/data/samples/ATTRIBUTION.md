# Sample data: sources and licenses

Small, unmodified samples of public datasets, committed so tests and simulations run offline. Rows were read through the Hugging Face dataset viewer on 2026-10-24.

| File | Source | Split, rows | License |
|---|---|---|---|
| `gsm8k_test.jsonl` | [openai/gsm8k](https://huggingface.co/datasets/openai/gsm8k), config `main` | test, rows 0–79 | MIT |
| `mmlu_part1.jsonl` | [cais/mmlu](https://huggingface.co/datasets/cais/mmlu): high_school_physics, conceptual_physics, high_school_mathematics, elementary_mathematics, high_school_biology | test, rows 0–24 of each | MIT |
| `mmlu_part2.jsonl` | [cais/mmlu](https://huggingface.co/datasets/cais/mmlu): college_biology, high_school_chemistry, astronomy, medical_genetics, high_school_computer_science | test, rows 0–24 of each | MIT |

GSM8K: Cobbe et al., "Training Verifiers to Solve Math Word Problems", arXiv:2110.14168.
MMLU: Hendrycks et al., "Measuring Massive Multitask Language Understanding", ICLR 2021, arXiv:2009.03300.

## Fields
- GSM8K: `question`, `answer` (the final number after `####`, commas removed), `steps` (count of `<<…>>` calculator annotations in the reference solution; one row, `gsm8k-test-24`, has none, so its value of 4 counts the solution's sentences instead).
- MMLU: `subject`, `question`, `choices` (4 options), `answer` (letter A–D).

## Known differences from the source
- The dataset viewer collapses line breaks into spaces, so multi-line questions (e.g. `mmlu-high_school_physics-4`, `mmlu-elementary_mathematics-5`) appear on one line.
- The viewer escapes some Markdown characters. These escapes were removed (e.g. `\>` → `>` in `mmlu-high_school_mathematics-11`).

These samples are for testing the pipeline, not for reporting benchmark scores. `scripts/fetch_datasets.py` downloads the full, original datasets on a machine that can reach Hugging Face.
