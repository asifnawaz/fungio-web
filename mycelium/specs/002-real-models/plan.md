# Implementation Plan: Real models on one GPU

**Branch**: `002-real-models` | **Date**: 2026-10-24 | **Spec**: [spec.md](spec.md)

## Summary

Swap the mocks for real models on one RTX 3090: a GSQ-RCO teacher served by llama.cpp, a ~1.5–2B student trained with TRL (SFT, logit distillation, GRPO with the RLCR reward), trustworthy evals, then (only if the spec 003 kill test says so) hidden-state HIKMAT keys, and finally GSQ + RCO builds of the student.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: llama.cpp (`llama-server`), transformers, TRL, one of Unsloth or Liger Kernel, EvalPlus, FAISS (optional)

**Storage**: cached teacher answers and top-k logits on disk (JSONL / arrays), reports as JSON

**Testing**: pytest on CPU (mock and simulated paths), GPU runs recorded in `research.md`

**Target Platform**: Linux or Windows PC, RTX 3090 24 GB, 32 GB RAM, NVMe SSD

**Project Type**: Python library + CLI (`mycelium`)

**Performance Goals**: measured, not assumed: teacher tokens/s, training time per epoch, HIKMAT lookup time

**Constraints**: 24 GB VRAM (train with the teacher stopped), keys only in environment variables, CI without a GPU

**Scale/Scope**: one teacher, one student, eval sets in the low thousands of problems

## Constitution Check

| Principle | Status |
|---|---|
| I. Honesty | Student must reach ECE < 0.1 and not hallucinate more than the base (SC-002). |
| II. Verification outside the model | Sandboxed code JUDGE and a second independent JUDGE (T007, T009). |
| III. Gated self-improvement | Memory work waits for the spec 003 verdict; autopilot gates unchanged. |
| IV. The exam is sacred | Private fingerprinted holdout, read only with `--final` (T008). |
| V. Measure, then claim | Every GPU number goes into `research.md` with command and hardware. |
| VI. Proven before novel | Off-the-shelf llama.cpp, TRL, GSQ, RCO; HIKMAT gated by a kill test. |
| VII. Modest hardware | Everything sized for one 3090. |
| IX. Secrets | `--teacher-api-key-env`, never a key on the command line. |
| X. Tests stay green | Mock and simulated paths stay in CI (FR-008). |

No violations.

## Project Structure

```text
specs/002-real-models/
├── spec.md  plan.md  research.md  quickstart.md  tasks.md
├── contracts/student-backend.md   # HFStudent interface (T010–T013)
└── checklists/requirements.md

mycelium/mycelium/
├── models/hf_student.py      # new: TrainableBackend over transformers (T010)
├── evals/real.py             # extended loaders (T006)
├── evals/sandbox.py          # new: container-backed code judge (T007)
└── ...                       # existing modules unchanged in shape
```

**Structure Decision**: extend the existing package; new backends implement the existing protocols so the pipeline doesn't change.

## Details

### Stack
| Part | Choice | Notes |
|---|---|---|
| Teacher serving | llama.cpp `llama-server` | `Qwen3.8-27B-GSQ-RCO-IQ3_S.gguf`, `-ngl 99 -c 32768`; MTP speculative decoding later |
| Teacher client | `models/openai_compat.py` + `models/cache.py` | already built and tested |
| Student base | newest ~1.5–2B Qwen with the same tokenizer family as the teacher | same tokenizer enables logit distillation; verify vocab match |
| Training | Hugging Face TRL + **one of** Unsloth / Liger Kernel | SFT, then GRPO with `rlcr.rlcr_reward`; LoRA to fit 24 GB |
| Logit distillation | store top-32 teacher logits per token | ~6–7 GB per 50M tokens |
| Evals | EvalPlus (HumanEval/MBPP), GSM8K, MATH-500, factual QA + unanswerables | loaders under `evals/real/` |
| Code sandbox | container (e.g. Docker with `--network none`, CPU, memory and time limits) | replaces `judge_code`'s plain subprocess for real model code |
| HIKMAT keys | mean-pooled middle-layer hidden state of the student | pick the layer by family recall (Q2) |
| Index | `numpy` < 100k records, `binary-ivf` beyond | measured in spec 001 |
| Quantization | GSQ + RCO (IST-DASLab repos) | budgets ~0.5 / 1 / 2 GB |

### Memory budget on the 3090
- Teacher IQ3_S: 11.8 GB, plus KV for 32k context (estimate a few GB; measure).
- Student 1.5–2B in bf16: ~3–4 GB for inference; LoRA training needs more, so train while the teacher is stopped. Teacher outputs are cached and logits are stored on disk first.

### Order
1. Teacher up + real-teacher e2e (validates the client against a real model).
2. Real evals + sandbox (so every later number is trustworthy).
3. Student backend: inference, then SFT, then GRPO-RLCR.
4. Spec 003 kill test with the student; real HIKMAT keys only if it says `pays`.
5. GSQ + RCO.
6. Write the results into `research.md` and the README.

### Risks
- Teacher format drift (missing ANSWER/CONFIDENCE lines): `parse_reply` falls back to 0.5 confidence. Track the rate and tune the system prompt.
- 24 GB pressure during training: stop the teacher and train from cached data.
- Tokenizer mismatch blocks logit distillation: fall back to sequence-level SFT on traces.
