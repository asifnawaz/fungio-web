# Tasks: MYCELIUM on phones and laptops (Draft)

**Blocked until** spec 002 T018–T019 are done. Before any task here: write `plan.md` from `.specify/templates/plan-template.md`, then update this list.

## Phase 1: Setup

- [ ] T001 [OWNER] Ask: "Which phone(s) should I target first, and is Android enough for v1?" Record the answer in `docs/decisions.md`.
- [ ] T002 Survey existing ways to run a GGUF on Android with llama.cpp (official examples, maintained apps); pick one in `plan.md` with reasons. No custom inference engine.

## Phase 2: User Story 1 - Answer offline on a phone (P1)

- [ ] T003 [US1] Run the spec 002 0.5 GB and 1 GB GGUF builds on the phone; measure tokens/s, peak RAM and battery drain for 50 GSM8K sample questions.
- [ ] T004 [US1] Compare on-device accuracy with the desktop run of the same GGUF (SC-002).

## Phase 3: User Story 2 - Memory on the device (P2, only if spec 003 = `pays`)

- [ ] T005 [US2] Port HIKMAT lookup with `binary-ivf` keys and CODON reranking; measure lookup time and bytes per record on the phone.
- [ ] T006 [US2] Run the golden-set health check and rollback on the device.

## Phase 4: User Story 3 - Laptop app (P3)

- [ ] T007 [US3] Package the student, memory and local server for laptops (8 GB RAM); run the e2e suite against it.
