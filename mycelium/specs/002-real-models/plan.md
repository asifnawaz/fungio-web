# Plan 002: real models

## Stack
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

## Memory budget on the 3090
- Teacher IQ3_S: 11.8 GB, plus KV for 32k context (estimate a few GB; measure).
- Student 1.5–2B in bf16: ~3–4 GB for inference; LoRA training needs more, so train while the teacher is stopped. Teacher outputs are cached and logits are stored on disk first.

## Order
1. Teacher up + real-teacher e2e (validates the client against a real model).
2. Real evals + sandbox (so every later number is trustworthy).
3. Student backend: inference, then SFT, then GRPO-RLCR.
4. Real HIKMAT keys.
5. GSQ + RCO.
6. Write the results into `research.md` and the README.

## Risks
- Teacher format drift (missing ANSWER/CONFIDENCE lines): `parse_reply` falls back to 0.5 confidence. Track the rate and tune the system prompt.
- 24 GB pressure during training: stop the teacher and train from cached data.
- Tokenizer mismatch blocks logit distillation: fall back to sequence-level SFT on traces.
