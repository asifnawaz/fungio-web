# Tasks 002: real models

Format: `[ ]` open, `[x]` done, `[P]` can run in parallel with other `[P]` tasks in the same phase. Each task lists files, the proof it is done, and its dependencies. Work top to bottom unless marked `[P]`. Tick a task only when its proof passes and `pytest -q` stays green.

## Phase 0: Setup (on the GPU PC)
- [ ] T001 Set up the environment: Python ≥3.10, CUDA drivers, `pip install -e ".[dev,faiss]"`, build or install llama.cpp with CUDA.
  Proof: `pytest -q` passes; `llama-server --version` prints.
- [ ] T002 Download the teacher: `hf download ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF Qwen3.8-27B-GSQ-RCO-IQ3_S.gguf --local-dir models`.
  Proof: file present, 11.8 GB. Depends: T001.
- [ ] T003 Serve the teacher: `llama-server -m models/Qwen3.8-27B-GSQ-RCO-IQ3_S.gguf -ngl 99 -c 32768 --port 8080`. Record VRAM use and tokens/s in `research.md`.
  Proof: `curl localhost:8080/v1/models` answers. Depends: T002.
- [ ] T004 Real-teacher smoke run: `python -m mycelium.cli e2e --teacher-url http://localhost:8080 --teacher-model qwen3.8-27b --out reports/real-teacher.json`.
  Proof: run completes; record the teacher's accuracy, abstain rate, and how often `CONFIDENCE:` was missing. Depends: T003.
- [ ] T005 [P] Optional hosted teacher: the same run with `--teacher-url https://api.deepseek.com --teacher-api-key-env DEEPSEEK_API_KEY` and the model id from DeepSeek's docs.
  Proof: report saved. The key never appears in files or shell history.

## Phase 1: Trustworthy evaluation
- [ ] T006 [P] Add `mycelium/evals/real/` loaders returning `Problem` lists for GSM8K, MATH-500, HumanEval+/MBPP+ (EvalPlus) and factual QA with unanswerable questions; a cache directory for downloads.
  Proof: `tests/test_real_loaders.py` with tiny fixture files (no network in tests).
- [ ] T007 [P] Code sandbox: `judge_code` runs inside a container (no network, CPU/memory/time limits) when available, otherwise the current subprocess path with a loud warning.
  Proof: tests show a network call and an infinite loop are both blocked.
- [ ] T008 Private holdout: a split never used for tuning, fingerprinted like `GoldenSet`; loaded only by a `--final` flag.
  Proof: test that tuning code paths cannot read it.
- [ ] T009 Second JUDGE implementation for math and QA, written independently; a CI check that both agree on a sample.
  Proof: agreement test passes.

## Phase 2: Real student
- [ ] T010 `models/hf_student.py`: `TrainableBackend` over a ~1.5–2B Qwen (transformers), emitting `ANSWER:`/`CONFIDENCE:` and reusing `parse_reply`. Verify the tokenizer matches the teacher family.
  Proof: inference test on a tiny model (CPU) behind a skip-if-no-torch marker.
- [ ] T011 SFT from verified teacher traces (`distill.build_distillation_set` output) with TRL + Unsloth **or** Liger, LoRA.
  Proof: holdout accuracy above the base student; numbers in `research.md`.
- [ ] T012 Top-k (32) teacher logit storage and a distillation loss; fall back to sequence-level if tokenizers differ.
  Proof: loss decreases on a tiny run; storage size per 1M tokens recorded.
- [ ] T013 GRPO with `rlcr.rlcr_reward` via TRL, plus the learnable-problem filter and dynamic sampling from `rlcr.py`.
  Proof: holdout ECE < 0.1, accuracy not lower, hallucination not higher.
- [ ] T014 Run the full pipeline with the real student and real teacher; compare to the mock report.
  Proof: report saved; differences explained in `research.md`.

## Phase 3: Real HIKMAT
- [ ] T015 Keys from mean-pooled middle-layer hidden states; script to pick the layer by same-family recall on the eval suites.
  Proof: chosen layer and recall table in `research.md`.
- [ ] T016 Payload = verified method text given as the hint message; measure loops/tokens saved per hit.
  Proof: HIKMAT days on real problems lower mean cost vs teacher-only at equal accuracy.
- [ ] T017 [P] Rerank `binary-ivf` shortlists from the 16-byte CODON codes instead of stored floats (memory for phones).
  Proof: same recall within 1 point; memory per record reported.

## Phase 4: Compression
- [ ] T018 GSQ + RCO the trained student at ~0.5 / 1 / 2 GB budgets (IST-DASLab/GSQ, IST-DASLab/RCO).
  Proof: quality-per-budget table; the 1 GB build keeps ≥95% of unquantized holdout accuracy.
- [ ] T019 [P] Serve the quantized student in llama.cpp and run the pipeline with it.
  Proof: e2e report saved.

## Phase 5: Speed (after the above)
- [ ] T020 [P] Teacher speculative decoding with the `-mtp` GGUF build (check llama.cpp docs for flags).
  Proof: tokens/s before and after.
- [ ] T021 [P] Batched HIKMAT lookups in autopilot reviews and health checks.
  Proof: review time before and after.
- [ ] T022 DeepSeek-V4.1-Flash GSQ-RCO on Strata (confirm the canonical repo first) as the testbed for task-aware expert prefetch: log expert usage per task, simulate global vs task-aware caches offline, and only then change the engine.
  Proof: simulated cache hit rates in `research.md`.

## Phase 6: Open-source launch chores
- [ ] T023 Add the full AGPL-3.0 `LICENSE` text and SPDX headers.
- [ ] T024 Move `mycelium/` into its own repository (history via `git subtree split --prefix=mycelium`), with CI running `pytest` and ruff.
- [ ] T025 [P] `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, issue templates, "good first issue" labels.
- [ ] T026 [P] Optional donation link (Open Collective or GitHub Sponsors, depending on payout support in the owner's country); never gate features.
