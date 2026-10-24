# Tasks 001: v0.1 pipeline (complete)

- [x] T001 JUDGE: math, QA, code-in-subprocess verifiers with caching (`evals/judges.py`)
- [x] T002 Metrics: ECE, Brier, AUROC, hallucination and abstain rates (`evals/metrics.py`)
- [x] T003 Synthetic suites with problem families and unanswerable QA (`evals/datasets.py`)
- [x] T004 Mock teacher and student with realistic failure modes (`models/mock.py`)
- [x] T005 P1 distillation with rejection sampling (`distill.py`)
- [x] T006 P2 RLCR reward, GRPO advantages, dynamic sampling (`rlcr.py`)
- [x] T007 P3 TRIAGE router, threshold tuning, Pareto front, teacher-only fallback (`router.py`)
- [x] T008 CODON 2-bit codec (`hikmat/codec.py`)
- [x] T009 HIKMAT memory: admission, merge, budget, eviction, expiry, versioning (`hikmat/memory.py`)
- [x] T010 Autopilot: shadow review, golden fingerprint, ratchet, rollback (`autopilot.py`)
- [x] T011 Attack scenarios in the e2e run (`pipeline.py`)
- [x] T012 Fix: router `stop_at` mismatch; lookup-first routing; monotonic ids after rollback
- [x] T013 Vector indexes: numpy (exact), faiss-hnsw, binary-ivf (XOR + IVF) with a benchmark (`hikmat/index.py`, `bench.py`)
- [x] T014 OpenAI-compatible teacher backend + response cache (`models/openai_compat.py`, `models/cache.py`)
- [x] T015 Simulated HTTP teacher and full pipeline over HTTP (`sim_teacher.py`, `tests/test_sim_teacher.py`)
- [x] T016 API key via environment variable only (`--teacher-api-key-env`)
- [x] T017 Real questions: 80 GSM8K + 250 MMLU (10 science/math subjects) committed with attribution; loaders and a full-download script (`evals/real.py`, `data/samples/`, `scripts/fetch_datasets.py`)
- [x] T018 Multiple-choice domain: prompt format, letter parsing that doesn't mistake the article "A" for option A, judging (`evals/judges.py`)
- [x] T019 Complex scenario: topic drift, subject-level skills, overconfidence where weak (Dunning-Kruger), teacher blind spot (`pipeline.py`, `models/mock.py`)
- [x] T020 Simulated teacher answers the real samples, with per-family accuracy overrides (`sim_teacher.py`)
- [x] T021 Anti-hallucination, anti-reversal and anti-slop rules for agents (`AGENTS.md`)

## Convergence

Gaps found after the first 21 tasks, while answering "do insights work?" (2026-10-24). All done, all tested.

- [x] T022 Problems carry a template; insights record the template they came from; merging keeps sources apart (`types.py`, `evals/datasets.py`, `hikmat/memory.py`)
- [x] T023 Mock hint effect depends on template and family: full gain on its own template, a transfer fraction for procedures, none for facts, a fixed penalty for the wrong family (`models/mock.py`, `tests/test_insights.py`)
- [x] T024 Autopilot promotes an insight only on a measurable gain, not merely no harm (`autopilot.py`)
- [x] T025 No-memory ablation, repeat rate and retrieval-match stats per HIKMAT day; `insights` sweep command (`pipeline.py`, `insights.py`, `cli.py`)
- [x] T026 GSM-Symbolic committed verbatim and a `--suite symbolic` (`data/samples/`, `evals/real.py`, `pipeline.py`)
- [x] T027 Fix: a negative `hint_gain` times the wrong-family factor turned poison into help (regression test in `tests/test_insights.py`)
