---
description: "Tasks for real models on one GPU"
---

# Tasks: Real models on one GPU

**Input**: `specs/002-real-models/` (spec.md, plan.md, research.md, quickstart.md)

**Tests**: Required (constitution X). Tick a task only when its proof passes and `pytest -q` stays green.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel with other `[P]` tasks in the same phase
- **[Story]**: US1–US6 from spec.md
- Each task names its files, the proof it is done, and dependencies. IDs are stable; other docs refer to them.

## Phase 1: Setup (on the GPU PC)

- [ ] T001 [US1] Environment: Python ≥3.10, CUDA drivers, `pip install -e ".[dev,faiss]"`, llama.cpp built or installed with CUDA.
  Proof: `pytest -q` passes; `llama-server --version` prints.
- [ ] T002 [US1] Download the teacher: `hf download ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF Qwen3.8-27B-GSQ-RCO-IQ3_S.gguf --local-dir models`.
  Proof: file present, 11.8 GB. Depends: T001.
- [ ] T003 [US1] Serve it: `llama-server -m models/Qwen3.8-27B-GSQ-RCO-IQ3_S.gguf -ngl 99 -c 32768 --port 8080`. Record VRAM use and tokens/s in `research.md`.
  Proof: `curl localhost:8080/v1/models` answers. Depends: T002.

## Phase 2: Foundational (trustworthy evaluation; blocks every quality claim)

- [ ] T006 [P] [US2] Extend `mycelium/evals/real.py`: GSM8K, MMLU and GSM-Symbolic loaders exist. Add MATH-500, HumanEval+/MBPP+ (EvalPlus) and factual QA with unanswerable questions; run `scripts/fetch_datasets.py` on the PC and evaluate on the full sets.
  Proof: loader tests with tiny fixture files (no network in tests); full-set teacher accuracy in `research.md`.
- [ ] T007 [P] [US2] Code sandbox: `judge_code` runs inside a container (no network, CPU/memory/time limits) when available, otherwise the subprocess path with a loud warning.
  Proof: tests show a network call and an infinite loop are both blocked.
- [ ] T008 [US2] Private holdout: a split never used for tuning, fingerprinted like `GoldenSet`; loaded only with a `--final` flag.
  Proof: test that tuning code paths cannot read it.
- [ ] T009 [US2] Second JUDGE implementation for math and QA, written independently; a CI check that both agree on a sample.
  Proof: agreement test passes.

**Checkpoint**: numbers from here on can be trusted.

## Phase 3: User Story 1 - Real teacher (Priority: P1) 🎯 MVP

**Independent Test**: T004's report exists and was produced without code changes.

- [ ] T004 [US1] Real-teacher run: `python -m mycelium.cli e2e --teacher-url http://localhost:8080 --teacher-model qwen3.8-27b --out reports/real-teacher.json`.
  Proof: run completes; record the teacher's accuracy, abstain rate and how often `CONFIDENCE:` was missing. Depends: T003.
- [ ] T005 [P] [US1] Optional hosted teacher: the same run with `--teacher-url https://api.deepseek.com --teacher-api-key-env DEEPSEEK_API_KEY` and the model id from DeepSeek's docs.
  Proof: report saved; the key never appears in files or shell history.

## Phase 4: User Story 3 - Calibrated real student (Priority: P2)

**Independent Test**: holdout table (accuracy, ECE, hallucination) for base, SFT and RLCR student in `research.md`.

- [ ] T010 [US3] `models/hf_student.py`: `TrainableBackend` over a ~1.5–2B Qwen (transformers), emitting `ANSWER:`/`CONFIDENCE:` and reusing `parse_reply`. Verify the tokenizer matches the teacher family.
  Proof: inference test on a tiny model (CPU) behind a skip-if-no-torch marker.
- [ ] T011 [US3] SFT from verified teacher traces (`distill.build_distillation_set` output) with TRL + Unsloth **or** Liger, LoRA.
  Proof: holdout accuracy above the base student; numbers in `research.md`.
- [ ] T012 [US3] Top-k (32) teacher logit storage and a distillation loss; fall back to sequence-level if tokenizers differ.
  Proof: loss decreases on a tiny run; storage size per 1M tokens recorded.
- [ ] T013 [US3] GRPO with `rlcr.rlcr_reward` via TRL, plus the learnable-problem filter and dynamic sampling from `rlcr.py`.
  Proof: holdout ECE < 0.1, accuracy not lower, hallucination not higher.
- [ ] T014 [US3] Full pipeline with the real student and real teacher; compare to the mock report.
  Proof: report saved; differences explained in `research.md`.

## Phase 5: User Story 4 - Memory that pays on real models (Priority: P2)

**Independent Test**: spec 003's verdict, then HIKMAT days on real problems vs teacher-only.

- [ ] T015a [US4] **Kill test first**: run spec 003 (`python -m mycelium.cli killtest --url …`, see `specs/003-insight-kill-test/quickstart.md`) with the real student.
  Proof: verdict recorded in `docs/decisions.md`. `kill` stops T015–T017; `inconclusive` means run more first.
- [ ] T015 [US4] Keys from mean-pooled middle-layer hidden states; script to pick the layer by same-family recall on the eval suites.
  Proof: chosen layer and recall table in `research.md`. Depends: T015a = `pays`.
- [ ] T016 [US4] Payload = verified method text given as the hint message; measure tokens saved per hit.
  Proof: HIKMAT days on real problems lower mean cost vs teacher-only at equal accuracy. Depends: T015.
- [ ] T017 [P] [US4] Rerank `binary-ivf` shortlists from the 16-byte CODON codes instead of stored floats (memory for phones).
  Proof: same recall within 1 point; memory per record reported.

## Phase 6: User Story 5 - Compressed student (Priority: P3)

- [ ] T018 [US5] GSQ + RCO the trained student at ~0.5 / 1 / 2 GB budgets (IST-DASLab/GSQ, IST-DASLab/RCO).
  Proof: quality-per-budget table; the 1 GB build keeps ≥95% of unquantized holdout accuracy.
- [ ] T019 [P] [US5] Serve the quantized student in llama.cpp and run the pipeline with it.
  Proof: e2e report saved.

## Phase 7: User Story 6 - Speed (Priority: P3, after the above)

- [ ] T020 [P] [US6] Teacher speculative decoding with the `-mtp` GGUF build (check llama.cpp docs for flags).
  Proof: tokens/s before and after.
- [ ] T021 [P] [US6] Batched HIKMAT lookups in autopilot reviews and health checks.
  Proof: review time before and after.
- [ ] T022 [US6] DeepSeek-V4.1-Flash GSQ-RCO on Strata (confirm the canonical repo first) as the testbed for task-aware expert prefetch: log expert usage per task, simulate global vs task-aware caches offline, and only then change the engine.
  Proof: simulated cache hit rates in `research.md`.

## Phase 8: Polish (open-source launch chores)

- [ ] T023 Add the full AGPL-3.0 `LICENSE` text and SPDX headers (license changes need the owner's approval).
- [ ] T024 Move `mycelium/` into its own repository (history via `git subtree split --prefix=mycelium`), with CI running `pytest` and ruff.
- [ ] T025 [P] `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, issue templates, "good first issue" labels.
- [ ] T026 [P] Optional donation link (Open Collective or GitHub Sponsors, depending on payout support in the owner's country); never gate features.

## Dependencies & Execution Order

- Setup (T001–T003) → Foundational (T006–T009) → US1 (T004–T005).
- US3 needs US1 (teacher traces). US4 needs a real student (T010) for T015a, and T015a = `pays` for T015–T016.
- US5 needs US3. US6 can start after US1 but only matters after US3.
- Phase 8 is independent; T023 needs the owner's approval.

## Implementation Strategy

US1 and the foundational evals first: a real teacher with trustworthy numbers. Then US3, then the kill test, which decides whether US4 is worth building.
