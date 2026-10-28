---
description: "Tasks for real models on one GPU"
---

# Tasks: Real models on one GPU

**Input**: `specs/002-real-models/` (spec.md, plan.md, research.md, quickstart.md, contracts/student-backend.md). Execution order across specs: `specs/ROADMAP.md`.

**Tests**: Required (constitution X). Tick a task only when its proof passes and `pytest -q` stays green.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel with other `[P]` tasks in the same phase
- **[Story]**: US1–US6 from spec.md
- Each task names its files, the proof it is done, and dependencies. IDs are stable; other docs refer to them.

## Phase 1: Setup (on the GPU PC)

- [ ] T001 [US1] Environment. Run `python -m mycelium.cli doctor --network` first; it reports OS, GPU, VRAM, free disk, and missing tools. Then: Python ≥3.10 venv, `pip install -e ".[dev,faiss]"`, `pip install -U huggingface_hub`, NVIDIA driver with CUDA, and llama.cpp with CUDA (Linux: build from source with CUDA enabled; Windows: the CUDA build from the llama.cpp GitHub releases page; check the release notes for the exact asset and flags, don't guess). Need about 40 GB free disk.
  Proof: `doctor` shows `"GPU": true`; `pytest -q` passes; `llama-server --version` prints. Write the doctor output into `research.md`.
- [x] T001b [US3] **Small-model baseline (P0), before the teacher.** Done 2026-10-24 on the cloud container CPU (see `research.md`); on the PC, rerun only to record GPU speed. `hf download unsloth/Qwen3.5-2B-MTP-GGUF Qwen3.5-2B-Q8_0.gguf --local-dir models`; `llama-server -m models/Qwen3.5-2B-Q8_0.gguf -ngl 99 -c 16384 -np 4 --reasoning off --spec-type draft-mtp --port 8081`; send one request with `curl` and read the raw reply (needs `ANSWER:` and `CONFIDENCE:` lines; if it is cut off or full of thinking text, raise `--max-tokens` or check the chat template (the Qwen3.5-2B card says it runs in non-thinking mode by default)); then `python -m mycelium.cli baseline --url http://localhost:8081 --model qwen3.5-2b --suite real --workers 4 --out reports/baseline-real.json` and the same with `--suite symbolic`.
  Proof: both tables, tokens/s, VRAM use and the share of replies with confidence exactly 0.5 in `research.md` under "Baseline: untrained Qwen3.5-2B". Depends: T001.
- [ ] T001c [US3] **Baseline of the student we train, `LiquidAI/LFM3-1.7B`** (owner's decision 2026-10-28, `docs/decisions.md`). Running on the cloud CPU since 2026-10-28. Needs llama.cpp master `8ca4060` or newer (`lfm3` support). `hf download LiquidAI/LFM3-1.7B-GGUF LFM3-1.7B-Q8_0.gguf --local-dir models`; `llama-server -m models/LFM3-1.7B-Q8_0.gguf -ngl 99 -c 16384 -np 4 --reasoning off --jinja --port 8081`; then the six `baseline` runs with `--model lfm3-1.7b`, the same seeds and the same `--limit`s as T001b. On a CPU with AMX, build without it (see `research.md`): the native build segfaults with two requests in flight.
  Proof: table in `research.md` under "Baseline: untrained LFM3-1.7B", side by side with T001b. **Every later student number is compared with this.** Depends: T001.
- [ ] T002 [US1] Download the teacher: `hf download ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF Qwen3.8-27B-GSQ-RCO-IQ3_S.gguf --local-dir models`.
  Proof: file present, 11.8 GB. Depends: T001.
- [ ] T003 [US1] Serve it: `llama-server -m models/Qwen3.8-27B-GSQ-RCO-IQ3_S.gguf -ngl 99 -c 32768 --port 8080`. Record VRAM use and tokens/s in `research.md`.
  Proof: `curl localhost:8080/v1/models` answers. Depends: T002.

## Phase 2: Foundational (trustworthy evaluation; blocks every quality claim)

- [ ] T006 [P] [US2] Extend `mycelium/evals/real.py` and `scripts/fetch_datasets.py` with these sources (ids and licenses checked 2026-10-24, see `specs/ROADMAP.md`): `HuggingFaceH4/MATH-500` (math, final answer in `\boxed{}`; confirm the license at github.com/openai/prm800k before committing any rows), `evalplus/humanevalplus` and `evalplus/mbppplus` (code, Apache-2.0; tests run through JUDGE's sandbox), `basicv8vc/SimpleQA` (short facts, MIT; a 2B student should mostly abstain), `truthfulqa/truthful_qa` (Apache-2.0). Unanswerable questions keep coming from `pipeline._unanswerables` (fictional entities). Downloads go to `data/full/` (gitignored); only small MIT/Apache samples may be committed, with `ATTRIBUTION.md` rows.
  Proof: loader tests with tiny fixture files (no network in tests); full-set teacher accuracy per source in `research.md`.
  Progress 2026-10-24: `scripts/fetch_datasets.py --evals` (MATH-500 500, HumanEval+ 164, MBPP+ 378, SimpleQA 4,326 rows into `data/full/`), loaders `load_math500/humanevalplus/mbppplus/simpleqa` and `load_eval_source`, judges for MATH expressions (`math-verify` when installed, normalized LaTeX otherwise) and SimpleQA short answers, `baseline --suite <source> --limit N`, fixture tests in `tests/test_eval_sources.py`. Reference solutions pass the code judge (EvalPlus needs a 30 s timeout). TruthfulQA left out: its multiple-choice sets have up to 13 options and free-form answers need a model grader. Still open: teacher accuracy per source (needs the PC).
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

- [ ] T010 [US3] `models/hf_student.py`: `HFStudent` for `LiquidAI/LFM3-1.7B`, exactly as `contracts/student-backend.md` says. Add `torch`, `transformers`, `peft`, `trl` as a new optional extra `student` in `pyproject.toml` (not in the base install). First check whether the installed `transformers` loads `lfm3` without `trust_remote_code`; if remote code is needed, pin the model revision and record it.
  Proof: `tests/test_hf_student.py` passes with torch installed and is skipped without it; base-model accuracy and ECE on the holdout in `research.md`.
- [ ] T011 [US3] SFT from verified teacher traces (`distill.build_distillation_set` output) with TRL + LoRA. Before starting, check whether Unsloth and Liger Kernel support the `lfm3` architecture (their docs or release notes); use one that does, or plain TRL + PEFT with gradient checkpointing. Record the choice in `docs/decisions.md`. Stop the teacher server while training.
  Proof: holdout accuracy above the base student; numbers in `research.md`. Depends: T004 (traces), T010.
- [ ] T012 [US3] Top-k (32) teacher logit storage and a distillation loss. The tokenizers differ (LFM3 128,000 vs Qwen3.8 248,320 tokens), so this needs a cross-tokenizer loss: check TRL's docs for its GOLD trainer / ULD loss first (unverified that it exists in the installed version); if nothing fits, skip T012 and keep sequence-level distillation (T011) and record that.
  Proof: loss decreases on a tiny run; storage size per 1M tokens recorded.
- [ ] T013 [US3] GRPO with `rlcr.rlcr_reward` via TRL, plus the learnable-problem filter and dynamic sampling from `rlcr.py`.
  Proof: holdout ECE < 0.1, accuracy not lower, hallucination not higher.
- [ ] T014 [US3] Full pipeline with the real student and real teacher; compare to the mock report.
  Proof: report saved; differences explained in `research.md`.

## Phase 5: User Story 4 - Memory that pays on real models (Priority: P2)

**Independent Test**: spec 003's verdict, then HIKMAT days on real problems vs teacher-only.

- [ ] T015a [US4] **Kill test first**: spec 003 T010b (`python -m mycelium.cli killtest --url …`, see `specs/003-insight-kill-test/quickstart.md`) with the trained student. A first reading with the untrained student (spec 003 T010a) runs much earlier.
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

- T001 → T001b (small-model baseline) → spec 003 T010a → teacher (T002–T003) → Foundational (T006–T009) → US1 (T004–T005).
- US3 needs US1 (teacher traces). US4 needs a real student (T010) for T015a, and T015a = `pays` for T015–T016.
- US5 needs US3. US6 can start after US1 but only matters after US3.
- Phase 8 is independent; T023 needs the owner's approval.

## Implementation Strategy

US1 and the foundational evals first: a real teacher with trustworthy numbers. Then US3, then the kill test, which decides whether US4 is worth building.
