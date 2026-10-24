# Roadmap: what to do next

Read `AGENTS.md` first, then this file. This is the single ordered list of every next task across all specs. The details of each task (files, proof, dependencies) live in that spec's `tasks.md`; this file says **which one is next**.

## Start-of-session protocol (every agent, every session)

1. `git pull`, then `python -m mycelium.cli doctor` (add `--network` on the PC). It says whether this machine can run `[CPU]` and `[GPU]` tasks and what is missing.
2. `pytest -q` and the ruff command from `AGENTS.md`. If either fails, fixing that is the task.
3. Walk the queue below from the top. The task is the **first row that is open, whose dependencies are done, and whose marker this machine can run**. Don't skip ahead, don't start two rows at once.
4. Row marked `[OWNER]`: ask Asif the exact question listed under "Questions for the owner" and wait. Don't proceed on a guess.
5. Row marked `[GATE]`: follow the branch the result picks, exactly as written in the spec's `research.md`.
6. Do the task as its `tasks.md` entry says. Put every number, the command and the hardware into that spec's `research.md`. Tick the task in `tasks.md` **and** set Status here to `done`. Commit with the task ID in the message (`002-T004: real-teacher run`).
7. Stuck (a step fails twice, or the spec doesn't say what to do): stop, write what you tried under "Open problems" in the spec's `research.md`, and ask the owner. Never invent a model id, flag, dataset or number to get past it.

## Markers

| Marker | Meaning |
|---|---|
| `[CPU]` | Runs anywhere, including the cloud container and CI |
| `[GPU]` | Needs the owner's PC (RTX 3090 24 GB, 32 GB RAM); `doctor` must show `"GPU": true` |
| `[OWNER]` | Needs Asif's answer or approval first |
| `[GATE]` | A decision point; branches are fixed in advance |

## Queue

On a machine without a GPU, take the first open `[CPU]` row instead; `[CPU]` rows don't depend on `[GPU]` rows unless listed.

| # | Task | Spec | Marker | Depends on | Status |
|---|---|---|---|---|---|
| 1 | T001 Environment on the PC (Python, CUDA, llama.cpp, `pip install -e ".[dev,faiss]"`) | 002 | `[GPU]` | — | open |
| 2 | T001b **Small-model baseline first**: serve the untrained student `Qwen3.5-2B-Q8_0.gguf` from `unsloth/Qwen3.5-2B-MTP-GGUF` (2.08 GB; `--reasoning off --spec-type draft-mtp -np 4`) and run `python -m mycelium.cli baseline` on the real and symbolic suites | 002 | `[GPU]` | 1 | done on the cloud CPU 2026-10-24 (numbers in spec 002 `research.md`); rerun on the PC only to record GPU speed |
| 3 | T010a Kill test, first reading, on the same student server | 003 | `[GPU]` `[GATE]` | 2 | done (cloud CPU): `kill` twice (full solution: 0.74 → 0.05; method only: 0.74 → 0.51); Q4 asked |
| 4 | T002 Download the teacher GGUF (11.8 GB) | 002 | `[GPU]` | 1 | open |
| 5 | T003 Serve the teacher; record VRAM and tokens/s | 002 | `[GPU]` | 4 | open |
| 6 | T004 Real-teacher e2e run | 002 | `[GPU]` | 5 | open |
| 7 | T006 Eval loaders (fixtures in tests) and full-set evaluation | 002 | `[CPU]` then `[GPU]` | — | open |
| 8 | T008 Private holdout behind `--final` | 002 | `[CPU]` | — | open |
| 9 | T009 Second, independent JUDGE for math and QA | 002 | `[CPU]` | — | open |
| 10 | T007 Container sandbox for the code JUDGE (needs Docker) | 002 | `[CPU]` | — | open |
| 11 | T010 `HFStudent` backend for `Qwen/Qwen3.5-2B` (contract: `specs/002-real-models/contracts/student-backend.md`) | 002 | `[CPU]` (tiny-model test) then `[GPU]` | — | open |
| 11a | T009–T011 **RSI kill test**, two STaR-style generations on the base student | 006 | `[GPU]` `[GATE]` | 11 | open |
| 12 | T011 SFT on verified teacher traces | 002 | `[GPU]` | 6, 11 | open |
| 13 | T012 Top-k logit distillation | 002 | `[GPU]` | 12 | open |
| 14 | T013 GRPO with the RLCR reward | 002 | `[GPU]` | 13 | open |
| 15 | T014 Full pipeline: real student + real teacher; compare with row 2's baseline | 002 | `[GPU]` | 14, 7–10 | open |
| 16 | T010b Kill test with the trained student (= 002 T015a) | 003 | `[GPU]` `[GATE]` | 14 | open |
| 16a | T013 RSI with the trained student | 006 | `[GPU]` `[GATE]` | 14, 11a ≠ `kill` | open |
| 17 | T013 Price the effect with `insights` | 003 | `[CPU]` | 16 | open |
| 18 | T015 Hidden-state HIKMAT keys | 002 | `[GPU]` | 16 = `pays` | open |
| 19 | T016 Method-text payloads, HIKMAT days on real problems | 002 | `[GPU]` | 18 | open |
| 20 | T017 CODON rerank for `binary-ivf` | 002 | `[CPU]` | 16 = `pays` | open |
| 21 | T017–T019 Kill-test follow-ups (own solutions, P1/P2, real retrieval) | 003 | `[GPU]` | 16 ≠ `kill` | open |
| 22 | T018 GSQ + RCO student builds (0.5 / 1 / 2 GB) | 002 | `[GPU]` | 14 | open |
| 23 | T019 Serve the quantized student; e2e | 002 | `[GPU]` | 22 | open |
| 24 | T020 Teacher speculative decoding (`-mtp` build) | 002 | `[GPU]` | 5 | open |
| 25 | T021 Batched HIKMAT lookups | 002 | `[CPU]` | — | open |
| 26 | T022 DeepSeek-V4.1-Flash on Strata, expert-prefetch simulation | 002 | `[GPU]` | 15 | open |
| 27 | T025 CONTRIBUTING, code of conduct, issue templates | 002 | `[CPU]` | — | open |
| 28 | T023 Full AGPL-3.0 text and SPDX headers | 002 | `[OWNER]` | — | open |
| 29 | T024 Own repository for `mycelium/` | 002 | `[OWNER]` | 28 | open |
| 30 | T026 Optional donation link | 002 | `[OWNER]` | 29 | open |
| 31 | Spec 004 On-device (phones) | 004 | Draft | 22, 23 | blocked |
| — | Spec 006 RSI mock loop (`python -m mycelium.cli rsi`) | 006 | `[CPU]` | — | done |
| 32 | Spec 005 Insight-sharing hub | 005 | Draft, `[OWNER]` | 19 and 16 = `pays` | blocked |
| 33 | Research track (FOLD, CODON latent language, INNER-SPROUT, …) | `docs/decisions.md` | `[OWNER]` | — | unscheduled |

Why the small model comes first: it is the baseline every later number is compared with (P0), it downloads in minutes (2 GB vs 11.8 GB), and it proves llama.cpp, the HTTP client and the answer format work on this PC before the big teacher is involved.

## Gates

- **Row 3 (first reading).** `pays` or `inconclusive`: continue the queue as is. `kill`: continue rows 4–15 (the student is needed anyway), but before row 16 ask the owner whether HIKMAT stays in scope (Q4).
- **Row 11a (RSI, base student).** `pays`: continue, and add spec 006 T012 (self-proposed problems) after row 16a. `plateau`: continue; try the other recipes in row 16a. `kill`: skip row 16a, record it, ask Q5.
- **Row 16 (trained student).** `pays`: rows 17–21. `inconclusive`: rerun with `--templates 100` before anything else. `kill`: mark rows 18–21 `dropped`, record it in `docs/decisions.md`, ask Q4.

## Questions for the owner (ask exactly these, then record the answer in `docs/decisions.md`)

- **Q1 (row 28):** "Should I add the full AGPL-3.0-or-later license text and SPDX headers now? This makes the license final for everything committed so far."
- **Q2 (row 29):** "What should the separate repository be called, and under which GitHub account? I'll move `mycelium/` there with its history."
- **Q3 (row 30):** "Which donation platform works for payouts in your country: GitHub Sponsors or Open Collective? Features stay free either way."
- **Q5 (RSI gate):** "Self-training on its own verified solutions didn't improve the exam (numbers: …). Options: (a) drop RSI and rely on distillation + RLCR, (b) retry with the trained student and more data, (c) try teacher-checked problems instead of self-checked ones. Which one?"
- **Q4 (gates):** "The kill test says hints don't help (numbers: …). Options: (a) drop HIKMAT memory and keep routing + calibration, (b) keep memory only for exact repeats (a cache), (c) try student-written insights or another payload format first (spec 003 T017), (d) train the student on hinted examples so it learns to use hints, then rerun T010b. Which one?" — asked 2026-10-24 after run 2.

## Already decided (don't re-decide without new evidence; see `docs/decisions.md`)

- Teacher: `ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF`, file `Qwen3.8-27B-GSQ-RCO-IQ3_S.gguf`.
- Student: `Qwen/Qwen3.5-2B` (reasons and checks below). Fallbacks: `Qwen/Qwen3.5-4B` if 2B is too weak, `Qwen/Qwen3.5-0.8B` for phones.
- Training: TRL with either Unsloth or Liger Kernel, never both.
- HIKMAT index: `numpy` up to ~100k records, `binary-ivf` beyond.
- GSM-Symbolic is evaluation-only; never train on it.
- The kill-test verdict rule is pre-registered and frozen.

## Facts checked on Hugging Face (2026-10-24)

| Item | Fact |
|---|---|
| `Qwen/Qwen3.5-2B` | Apache-2.0. 2B parameters, 24 layers laid out as 6 × (3 Gated DeltaNet + 1 Gated Attention), hidden size 2048, vocab 248,320 (tied embeddings), 262k context. Architecture `Qwen3_5ForConditionalGeneration` (has a vision encoder; we use text only). `config.json` names transformers 4.57.0.dev0. bf16 weights 4.55 GB. |
| Tokenizer match with the teacher | `Qwen/Qwen3.8-27B` has the same architecture family (`qwen3_5`), the same vocab size (248,320) and `vocab.json` / `merges.txt` of identical byte sizes (6,722,759 / 3,353,259). Likely identical; T010 must confirm by comparing token ids on sample text. |
| `unsloth/Qwen3.5-2B-GGUF` | `Qwen3.5-2B-Q8_0.gguf` 2.01 GB, `Qwen3.5-2B-Q4_K_M.gguf` 1.28 GB, `Qwen3.5-2B-BF16.gguf` 3.78 GB. |
| `unsloth/Qwen3.5-2B-MTP-GGUF` | Same quants with the MTP head kept (`Qwen3.5-2B-Q8_0.gguf` 2.08 GB). With llama.cpp `--spec-type draft-mtp`, measured fastest on CPU (see spec 002 `research.md`). Use this one. |
| `HuggingFaceH4/MATH-500` | `test.jsonl`, 500 problems from OpenAI's PRM800K split. The card has no license field; check `github.com/openai/prm800k` before committing any rows. |
| `evalplus/humanevalplus`, `evalplus/mbppplus` | Apache-2.0; MBPP+ has 378 test problems. |
| `basicv8vc/SimpleQA` | MIT, mirror of `openai/simple-evals` SimpleQA (short fact questions; a 2B model should mostly abstain). |
| `truthfulqa/truthful_qa` | Apache-2.0. |
| `rajpurkar/squad_v2` | CC-BY-SA-4.0 (has unanswerable questions, but share-alike): local evaluation only, never commit rows. |

Not checked yet (verify before relying on it): whether Unsloth and Liger support the `qwen3_5` architecture (Gated DeltaNet layers); the GitHub repos for GSQ and RCO; llama.cpp flags for `-mtp` speculative decoding.
