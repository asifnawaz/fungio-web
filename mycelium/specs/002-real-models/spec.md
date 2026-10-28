# Feature Specification: Real models on one GPU

**Feature Branch**: `002-real-models`

**Created**: 2026-10-24 (restructured to the Spec Kit template the same day)

**Status**: Next. Owner: Asif. Hardware: RTX 3090 (24 GB), 32 GB RAM, NVMe SSD.

**Input**: Spec 001 proved the plumbing with a mock student. Replace the mocks with real models on the owner's PC and check whether the v0.1 claims hold: honest, cheaper with use, safe self-improvement.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Real teacher, no code changes (Priority: P1)

The owner serves Qwen3.8-27B GSQ-RCO on the 3090 and runs the pipeline against it.

**Why this priority**: Teacher traces feed everything else (distillation, routing, memory).

**Independent Test**: `python -m mycelium.cli e2e --teacher-url http://localhost:8080 …` completes and the report lands in `research.md`.

**Acceptance Scenarios**:

1. **Given** `llama-server` with the IQ3_S GGUF, **When** the e2e run starts, **Then** it completes without code changes and reports how often `CONFIDENCE:` was missing.
2. **Given** a hosted API key in an environment variable, **When** `--teacher-api-key-env` names it, **Then** the run works and the key appears nowhere on disk.

---

### User Story 2 - Trustworthy evaluation (Priority: P1)

Full eval sets, a sandboxed code judge, a private holdout and a second independent JUDGE.

**Why this priority**: Every later number depends on it (constitution II, IV, V).

**Independent Test**: sandbox tests block network and infinite loops; the two JUDGEs agree on a sample; tuning code can't read the holdout.

**Acceptance Scenarios**:

1. **Given** model code that opens a socket or loops forever, **When** JUDGE runs it, **Then** it is stopped and marked wrong.
2. **Given** the private holdout, **When** threshold tuning runs, **Then** it cannot load it.

---

### User Story 3 - A calibrated real student (Priority: P2)

A ~1.5–2B student trained by SFT, logit distillation and GRPO with the RLCR reward says "I don't know" when it should and comes close to the teacher on math and code.

**Why this priority**: The cheap model is the point of the project; it must be honest before it is used.

**Independent Test**: holdout table for base, SFT and RLCR student.

**Acceptance Scenarios**:

1. **Given** the trained student, **When** it runs on the holdout, **Then** it reaches ≥85% of teacher accuracy on math and code, ECE < 0.1, and hallucination no higher than the base student.

---

### User Story 4 - Memory that pays on real models (Priority: P2)

HIKMAT keys come from the student's hidden states and payloads are verified method text. Before building it, the spec 003 kill test must say hints help.

**Why this priority**: Savings in the mock come from an assumed effect; this story only proceeds on evidence.

**Independent Test**: spec 003 verdict; then HIKMAT days on real problems vs teacher-only.

**Acceptance Scenarios**:

1. **Given** a `kill` verdict from spec 003, **When** planning US4, **Then** T015–T017 are dropped and the decision is recorded.
2. **Given** a `pays` verdict, **When** HIKMAT runs 5+ days on real problems, **Then** mean cost is below teacher-only at equal or better accuracy.

---

### User Story 5 - Compressed student (Priority: P3)

GSQ + RCO builds of the student at about 0.5 / 1 / 2 GB for laptops and phones.

**Why this priority**: Matters for reach, not for proving the system works.

**Independent Test**: quality-per-budget table.

**Acceptance Scenarios**:

1. **Given** the 1 GB build, **When** it runs on the holdout, **Then** it keeps ≥95% of the unquantized student's accuracy.

---

### User Story 6 - Speed (Priority: P3)

Speculative decoding for the teacher, batched HIKMAT lookups, and the Strata expert-prefetch testbed.

**Why this priority**: Only worth doing once the above works.

**Independent Test**: before/after tokens/s and review times.

**Acceptance Scenarios**:

1. **Given** the `-mtp` teacher build, **When** speculative decoding is on, **Then** tokens/s rise and outputs stay the same.

### Edge Cases

- The teacher drops the `ANSWER:`/`CONFIDENCE:` lines: `parse_reply` falls back to 0.5 confidence; track the rate and tune the prompt.
- 24 GB is too little to train with the teacher loaded: stop the teacher and train from cached traces.
- Student and teacher tokenizers differ: fall back from logit distillation to sequence-level SFT.
- The kill test is `inconclusive`: run more templates before any memory work.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Teacher = Qwen3.8-27B GSQ-RCO `IQ3_S` GGUF (11.8 GB) via `llama-server`; optionally a hosted OpenAI-compatible API with the key from an environment variable.
- **FR-002**: Real evals: GSM8K, MATH-500, HumanEval+/MBPP+ (EvalPlus), factual QA with unanswerable questions, and a private holdout never used for tuning.
- **FR-003**: The code JUDGE runs in a sandbox: no network, CPU, memory and time limits.
- **FR-004**: The student implements `TrainableBackend`: SFT, top-k logit distillation, GRPO with the RLCR reward, via TRL with **either** Unsloth **or** Liger Kernel.
- **FR-005**: The student answers with `ANSWER:` and `CONFIDENCE:` lines, parsed by the same `parse_reply`.
- **FR-006**: HIKMAT keys come from mean-pooled middle-layer hidden states; payload = verified method text. Only after spec 003 says `pays`.
- **FR-007**: GSQ + RCO quantization at fixed budgets, with quality per budget reported.
- **FR-008**: The CPU test suite keeps passing (mock and simulated paths stay).

### Key Entities

- **Teacher**: served GGUF model behind an OpenAI-compatible endpoint; answers are cached.
- **Student**: trainable ~1.5–2B model; later quantized builds per budget.
- **Eval suite**: full public sets plus a fingerprinted private holdout.
- **Insight**: verified method text keyed by a hidden-state vector (US4).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A real-teacher e2e run completes; report and teacher tokens/s recorded in `research.md`.
- **SC-002**: Trained student: ≥85% of teacher accuracy on math and code, ECE < 0.1, hallucination ≤ base student (holdout).
- **SC-003**: Spec 003 verdict recorded; if `pays`, HIKMAT over 5+ days lowers mean cost vs teacher-only at equal or better accuracy.
- **SC-004**: The 1 GB GSQ + RCO student keeps ≥95% of unquantized holdout accuracy.

## Assumptions

- The owner's PC has the stated hardware and can reach Hugging Face; this cloud container cannot.
- The student is `LiquidAI/LFM3-1.7B` (owner's decision 2026-10-28, replacing `Qwen/Qwen3.5-2B`). Its tokenizer differs from the teacher's, so token-level logit distillation needs a cross-tokenizer loss (T012); sequence-level distillation works as before.
- Out of scope: phones, the insight-sharing hub, FOLD/CODON/H-Net research. DeepSeek V4.1 Flash on Strata appears only as the US6 testbed (T022).
