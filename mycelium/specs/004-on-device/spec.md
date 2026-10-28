# Feature Specification: MYCELIUM on phones and laptops

**Feature Branch**: `004-on-device`

**Created**: 2026-10-24

**Status**: Draft, blocked. Starts only when spec 002 T018–T019 are done (quantized student builds exist and run in llama.cpp). Don't implement anything here before that; refine this spec instead.

**Input**: Owner's goal from the design discussions: the model runs everywhere, including phones, and keeps learning on the device; personal data never leaves it.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Answer offline on a phone (Priority: P1)

The owner installs a build of the quantized student on an Android phone and asks questions with no network. Answers carry a confidence and the model abstains when unsure.

**Why this priority**: Without a working on-device model nothing else in this spec matters.

**Independent Test**: The 0.5 GB or 1 GB GGUF from spec 002 T018 runs through llama.cpp on the phone; tokens/s, RAM and battery use are measured on the GSM8K and SimpleQA samples.

**Acceptance Scenarios**:

1. **Given** airplane mode, **When** the owner asks a GSM8K sample question, **Then** an answer with `ANSWER:` and `CONFIDENCE:` comes back and accuracy matches the desktop run of the same GGUF within 2 points.

---

### User Story 2 - Memory on the device (Priority: P2)

HIKMAT runs on the phone within a fixed byte budget: `binary-ivf` 8-byte keys, CODON 16-byte codes for reranking (spec 002 T017), same autopilot gates.

**Why this priority**: Only worth it if spec 003's verdict was `pays`.

**Independent Test**: Lookup time and memory per record on the phone; golden-set health checks run on the device.

**Acceptance Scenarios**:

1. **Given** 100k stored insights, **When** a lookup runs on the phone, **Then** it takes under 5 ms and memory stays within the budget (target to be confirmed by measurement).

---

### User Story 3 - Laptop app (Priority: P3)

The same student and memory as a desktop app for laptops without a big GPU.

**Independent Test**: Install on a laptop with 8 GB RAM; run the e2e suite against the local server.

### Edge Cases

- The phone has too little RAM for the 1 GB build: fall back to the 0.5 GB build or a smaller student (`Qwen/Qwen3.5-0.8B`).
- The device is low on battery: the router prefers abstaining or deferring over long thinking.

## Requirements *(mandatory)*

- **FR-001**: Inference through llama.cpp (no custom engine), using the spec 002 GGUF builds.
- **FR-002**: No network needed for answering; nothing personal is sent anywhere.
- **FR-003**: HIKMAT on device uses `binary-ivf` keys and CODON reranking, with a hard byte budget.
- **FR-004**: The autopilot's golden set and health checks run on the device; insights that fail are rolled back locally.

## Success Criteria *(mandatory)*

- **SC-001**: On a mid-range Android phone (model to be named by the owner), the 1 GB build answers at a speed the owner finds usable; tokens/s recorded.
- **SC-002**: On-device accuracy within 2 points of the desktop run of the same GGUF.

## Assumptions

- The owner names the test phone(s) before work starts (`[OWNER]`).
- Which app shell (a llama.cpp Android example, a Flutter/React Native wrapper, or another existing app) is decided in `plan.md` after checking what exists then; no custom engine.
