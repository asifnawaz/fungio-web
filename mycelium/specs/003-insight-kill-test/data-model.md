# Data model: HIKMAT kill test

## Source rows (`mycelium/data/samples/gsm_symbolic.jsonl`, Apple's format, read as is)

| Field | Meaning |
|---|---|
| `id` | template, 0–99 |
| `instance` | variant, 0–49; variant 0 is the donor, 1..K are targets |
| `question` | the problem text |
| `answer` | worked solution ending in `#### <number>`; the part before `####` is the insight shown as a hint |
| `original_id`, `original_question`, `original_answer` | the GSM8K test question the template came from |
| `canary` | contamination marker; never removed |

## Item (in memory)

`Item(problem: Problem, row: dict)`. `problem.template_key` is `gsm-symbolic-<id>`, `problem.family` is the step-count family (`math:gsm8k-short` ≤3 solution lines, `-medium` 4–5, `-long` ≥6).

## Hint (existing type, `mycelium/types.py`)

| Field | Kill-test value |
|---|---|
| `text` | `Problem: <donor question>\nVerified solution:\n<donor answer>` for real models; `method:<family>` for the mock |
| `similarity` | stand-in key similarity between target and donor |
| `record_id` | −1 (not from memory) |
| `source` | donor template key; the mock compares it with the target's to apply transfer |

## Trial (one JSON line in `--trials`)

| Field | Type | Meaning |
|---|---|---|
| `template` | int | template id |
| `instance` | int | target variant, 1..K |
| `condition` | `"none"` \| `"same"` \| `"other"` | which hint, if any |
| `correct` | bool | JUDGE result |
| `effort` | float | completion tokens; loops for the mock |
| `similarity` | float | donor similarity; 1.0 for `none` |

Unique key: (`template`, `instance`, `condition`). A rerun skips keys already in the file.

## Report (`--out`, schema in `contracts/report.schema.json`)

Accuracy and mean effort per condition; `d_acc_*` and `d_effort_*` (relative) for `same` and `other` against `none`; `ci95` with the 2.5th and 97.5th bootstrap percentiles; `mock_equivalents` (`math_skill`, `hint_gain`, `hint_gain_ci95`, `procedural_transfer`); `verdict`.
