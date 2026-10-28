# Sample data: sources and licenses

Unmodified samples of public datasets, committed so tests and simulations run offline. GSM8K and MMLU rows were read through the Hugging Face dataset viewer on 2026-10-24; GSM-Symbolic is the whole file, downloaded byte for byte.

| File | Source | Split, rows | License |
|---|---|---|---|
| `gsm8k_test.jsonl` | [openai/gsm8k](https://huggingface.co/datasets/openai/gsm8k), config `main` | test, rows 0–79 | MIT |
| `mmlu_part1.jsonl` | [cais/mmlu](https://huggingface.co/datasets/cais/mmlu): high_school_physics, conceptual_physics, high_school_mathematics, elementary_mathematics, high_school_biology | test, rows 0–24 of each | MIT |
| `gsm_symbolic.jsonl` | [apple/ml-gsm-symbolic](https://github.com/apple/ml-gsm-symbolic), `generated_data/GSM_symbolic.jsonl` (same bytes as `main/test.jsonl` in [apple/GSM-Symbolic](https://huggingface.co/datasets/apple/GSM-Symbolic)) | all 5,000 rows: 100 templates × 50 variants | Apple sample-code license, see `LICENSE-gsm-symbolic.txt` (the Hugging Face copy is labeled CC-BY-NC-ND-4.0) |
| `mmlu_part2.jsonl` | [cais/mmlu](https://huggingface.co/datasets/cais/mmlu): college_biology, high_school_chemistry, astronomy, medical_genetics, high_school_computer_science | test, rows 0–24 of each | MIT |

GSM8K: Cobbe et al., "Training Verifiers to Solve Math Word Problems", arXiv:2110.14168.
GSM-Symbolic: Mirzadeh et al., "GSM-Symbolic: Understanding the Limitations of Mathematical Reasoning in Large Language Models", arXiv:2410.05229.
MMLU: Hendrycks et al., "Measuring Massive Multitask Language Understanding", ICLR 2021, arXiv:2009.03300.

## Fields
- GSM8K: `question`, `answer` (the final number after `####`, commas removed), `steps` (count of `<<…>>` calculator annotations in the reference solution; one row, `gsm8k-test-24`, has none, so its value of 4 counts the solution's sentences instead).
- MMLU: `subject`, `question`, `choices` (4 options), `answer` (letter A–D).
- GSM-Symbolic: Apple's original fields (`id` = template, `instance` = variant, `question`, `answer` ending in `#### <number>`, `original_id`, `original_question`, `original_answer`, `canary`). `load_gsm_symbolic` reads them as they are.

## GSM-Symbolic license and use
- Downloaded on 2026-10-24 from raw.githubusercontent.com; SHA-256 `945055837b232bd9b56827b1e3a5aa019075f29e8ba4669d9a9df8b4439a291f`, checked by a test so the file stays unmodified.
- The GitHub repository ships it under Apple's sample-code license, which allows redistribution if the notice is kept (`LICENSE-gsm-symbolic.txt`). The Hugging Face copy of the same file is labeled CC-BY-NC-ND-4.0. The owner confirmed on 2026-10-24 that the project has the license to commit it. MYCELIUM is non-commercial, so it also stays within the stricter label.
- Every row carries Apple's canary string. Don't strip it: it lets anyone detect the rows in a training corpus. Use the file for evaluation and simulation; never train a model on it.
- Apple's name and marks are not used to endorse this project.

## Known differences from the source
- The dataset viewer collapses line breaks into spaces, so multi-line questions (e.g. `mmlu-high_school_physics-4`, `mmlu-elementary_mathematics-5`) appear on one line.
- The viewer escapes some Markdown characters. These escapes were removed (e.g. `\>` → `>` in `mmlu-high_school_mathematics-11`).

These samples are for testing the pipeline, not for reporting benchmark scores. `scripts/fetch_datasets.py` downloads the full, original datasets on a machine that can reach Hugging Face.
