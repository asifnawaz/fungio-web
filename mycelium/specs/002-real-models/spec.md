# Spec 002: Real models on one GPU

**Status:** Next · **Owner:** Asif · **Hardware:** RTX 3090 (24 GB), 32 GB RAM, NVMe SSD

## Why
Spec 001 proved the plumbing with a mock student. This spec replaces the mocks with real models on the owner's PC and checks whether the v0.1 claims hold for real: honest, cheaper with use, safe self-improvement.

## User stories
1. As the owner, I run a real teacher locally and the pipeline uses it without code changes.
2. As the owner, I train a real ~1.5–2B student that is calibrated (says "I don't know") and close to the teacher on math and code.
3. As the owner, HIKMAT keys come from the student's own hidden states, and memory makes repeat problem types measurably cheaper.
4. As the owner, the student is compressed with GSQ + RCO to exact size budgets (about 0.5 / 1 / 2 GB) for laptops and phones.
5. As an AI agent, every task names its files, its test, and the command that proves it is done.

## Requirements
- R1 Teacher: Qwen3.8-27B GSQ-RCO `IQ3_S` GGUF (11.8 GB) via `llama-server`. Optional: a hosted API (DeepSeek) through `OpenAICompatBackend` with the key from an environment variable.
- R2 Real evals: GSM8K, MATH-500, HumanEval/MBPP (via EvalPlus), and factual QA including unanswerable questions; a private holdout never used for tuning.
- R3 Code sandbox for JUDGE: container or equivalent, no network, CPU, memory and time limits.
- R4 Student backend implementing `TrainableBackend`: SFT, top-k logit distillation, and GRPO with the RLCR reward, via TRL with **either** Unsloth **or** Liger Kernel.
- R5 Student output format: `ANSWER:` + `CONFIDENCE:` lines, parsed by the same `parse_reply`.
- R6 HIKMAT keys from mean-pooled middle-layer hidden states; payload = verified method text (later: latent warm start).
- R7 GSQ + RCO quantization of the student at fixed budgets; report quality per budget.
- R8 All of the above keeps passing the CPU test suite (mock and sim paths stay).

## Acceptance
- A real-teacher e2e run completes and its report lands in `specs/002-real-models/research.md`.
- On the holdout, the trained student reaches ≥85% of teacher accuracy on math and code, ECE < 0.1, and hallucination no higher than the base student.
- HIKMAT over 5+ simulated days lowers mean cost versus teacher-only at equal or better accuracy.
- A GSQ + RCO student at the 1 GB budget keeps ≥95% of the unquantized student's holdout accuracy.

## Out of scope
Phones, the insight-sharing hub, FOLD/CODON/H-Net research, and DeepSeek V4.1 Flash on Strata. These are tracked as later tasks or in the research track.
