# Research: HIKMAT kill test

## Pre-registration (written 2026-10-24, before any real-model run)

The rules below are implemented in `mycelium/killtest.py:verdict` and must not change after a real run has been seen. A change needs a dated entry in `docs/decisions.md` and a fresh run.

**Hypotheses**
- **H1 (primary):** a verified solution of the same template helps on a new variant: higher accuracy, or the same accuracy with fewer tokens.
- **H2 (secondary):** a verified solution of a different template of the same size helps less, or hurts. This is the cost of a retrieval near-miss.

**Measures** (paired per target, 95% intervals by bootstrap over templates, 2,000 draws)
- `d_acc_same` = accuracy(same) − accuracy(none)
- `d_effort_same` = (tokens(same) − tokens(none)) / tokens(none)
- the same two for `other`.

**Verdict on H1**
- `pays` if the `d_acc_same` interval is above 0, **or** if tokens drop by ≥10% (point estimate), the token interval is below 0, and the accuracy interval's lower end is ≥ −0.02.
- `kill` if the accuracy interval is entirely below 0 (hints make answers worse, whatever they save), **or** if the accuracy interval's upper end is ≤ +0.02 and the token interval's lower end is ≥ −5% (no meaningful gain on either axis).
- `inconclusive` otherwise; rerun with more templates (up to 100) or variants (up to 49).

**What each verdict triggers**
- `pays`: continue spec 002 T015–T016 (real HIKMAT keys and payloads); use the fitted `hint_gain` in `insights` to size the expected saving.
- `kill`: stop memory feature work; record it; rethink HIKMAT (for example, store only exact-repeat answers, or move the effort into training).
- `inconclusive`: run more problems before deciding anything.

**Sample size.** Default 50 templates × 10 variants = 500 targets, 1,500 calls. On the mock, 30 templates × 10 variants gave a `d_acc_same` interval about ±0.03 wide (`hint_gain` 0.1: +0.053, interval +0.025 to +0.085), so 500 targets should resolve an accuracy change of about 0.04. A real model's variance may differ; the bootstrap reports what was actually achieved.

## Real runs

### Run 1: untrained Qwen3.5-2B, full worked solution as the hint (T010a), 2026-10-24

Cloud container CPU (4-core Xeon @ 2.10GHz, no GPU), llama.cpp `8e5a58d`, `unsloth/Qwen3.5-2B-MTP-GGUF` `Qwen3.5-2B-Q8_0.gguf`, `llama-server -c 16384 -np 4 -t 4 --reasoning off --spec-type draft-mtp`.
Command: `python -m mycelium.cli killtest --url http://127.0.0.1:8081 --model qwen3.5-2b --templates 20 --variants 5 --workers 4` (300 trials, ~27 min). Smaller than the planned 50 × 10 to fit the CPU; the effect was large enough to decide.

| Condition | Accuracy | Mean tokens |
|---|---|---|
| none | 0.740 | 396.4 |
| same | 0.050 | 17.1 |
| other | 0.080 | 36.9 |

same − none: accuracy −0.690 [−0.830, −0.540], tokens −95.7%. other − none: accuracy −0.660 [−0.810, −0.510]. **Verdict (pre-registered rule): `kill`** for this payload.

Why: with the donor's worked solution in the prompt, the model stopped reasoning (13–19 tokens instead of ~400) and either copied the donor's final answer or guessed. In a 16-question check, 6 replies were exactly the donor's answer; only 2 of 16 targets share the donor's answer. This is the "semantic cache" failure `docs/decisions.md` warned about: an insight that carries a final answer gets copied when the numbers differ.

### Amendment, registered 2026-10-24 before its run: H1b, method-only payload

Same design, rules, verdict function and server settings as run 1. Only the payload changes: the donor's solution steps with every number replaced by a placeholder (`<a>`, `<b>`, …), no final answer, and an instruction to apply the steps to the new numbers (`--payload method`, `killtest.method_payload`). The `none` trials of run 1 are reused (same templates, variants, seed and server). If H1b is also `kill`, HIKMAT's hint payloads don't help this model and roadmap Q4 goes to the owner.

## Harness checks (mock and simulated teacher, 4-core Xeon container)

Mock student, known parameters, `analyze` with the calibration fit (`python -c` runs in this session):

| True `hint_gain` / transfer / math skill | Templates × variants | Fitted `hint_gain` [95%] | Fitted transfer | Verdict |
|---|---|---|---|---|
| 0.4 / 0.25 / 0.45 | 50 × 10 | 0.38 [0.33, 0.44] | 0.16 | pays |
| 0.4 / 0.25 / 0.45 (seed 7) | 50 × 10 | 0.33 [0.27, 0.40] | 0.26 | pays |
| 0.4 / 0.25 / 0.60 | 20 × 10 | 0.38 [0.27, 1.50] | 0.31 | pays |
| 0.1 / 0 / 0.50 | 30 × 10 | 0.16 [0.08, 0.23] | 0.00 | pays |
| 0.2 / 0.5 / 0.45 | 50 × 10 | 0.23 [0.16, 0.30] | 0.58 | pays |
| 0.4 / 0.25 / 0.60 | 100 × 49 | 0.40 [0.37, 0.44] | 0.25 | pays |
| 0 and −0.2 | 30 × 10 | — | — | kill |

The `hint_gain` interval contained the true value in every case. Transfer is much noisier (the `other` effect is small) and should be read as a rough number.

Two estimators were tried and dropped:
- **Logit of mean accuracies** recovered 0.28 for a true 0.4: the mock also stops thinking earlier when hinted, so part of the gain turns into fewer loops, and averaging over problems of different difficulty shrinks the logit.
- **Fitting on all 49 variants** of the measured templates recovered 0.48 for a true 0.4: variants 1–10 happen to be harder for the mock than 1–49, so the fitted base skill was off. The fit now runs on exactly the measured problems, averaged over 5 mock seeds, and matches differences rather than levels.

Simulated teacher over HTTP (10 templates × 5 variants): the run completes, token counts come from the server, the resume path makes no calls on rerun. The simulated teacher ignores hint content, so its verdict (`kill`) says nothing about real models.

## Related work (checked on Hugging Face Papers, 2026-10-24)

- **GSM-Symbolic** (arXiv 2410.05229): per its abstract, models show noticeable variance across instantiations of the same question, accuracy drops when only the numbers change, and adding one irrelevant clause drops performance by up to 65%. This is why the `other` condition matters: a near-miss worked example may act like an irrelevant clause.
- **Buffer of Thoughts** (arXiv 2406.04271): stores reusable "thought templates" in a meta-buffer and retrieves them per problem; reports gains in accuracy and efficiency. Closest published design to HIKMAT's method payloads.
- **MemPrompt** (arXiv 2201.06009, "Memory-assisted prompt editing to improve GPT-3 after deployment"): pairs a model with a memory of feedback and improves accuracy without retraining.

None of these measured the same thing on a ~2B student with GSM-Symbolic's controlled variants, so they set expectations but don't replace this test.
