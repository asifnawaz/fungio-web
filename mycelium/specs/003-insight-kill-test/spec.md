# Feature Specification: HIKMAT kill test on GSM-Symbolic

**Feature Branch**: `003-insight-kill-test` (developed on `claude/mycelium-mock-pipeline`)

**Created**: 2026-10-24

**Status**: Harness done and checked on the mock and the simulated teacher; the real-model run is pending (needs a real student, see spec 002)

**Input**: Owner: "Insights test karne hain hamein plan ke mutabiq, Apple ka data istemal karlo" (test whether insights work, as planned, using Apple's GSM-Symbolic data).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Get a verdict on whether a stored method helps (Priority: P1)

The owner points the kill test at a real model on the GPU PC and runs one command. For each sampled GSM-Symbolic template, the model solves new variants with no hint, with the verified solution of the same template's variant 0, and with the verified solution of a different template of the same size. The report gives accuracy and tokens per condition, paired differences with 95% intervals, and a verdict decided by rules written down before the run.

**Why this priority**: Every saving HIKMAT shows today comes from an assumed hint effect (`hint_gain` in the mock). If a real hint doesn't help, memory features are wasted work. This is the cheapest test that can stop that.

**Independent Test**: `python -m mycelium.cli killtest --mock` (the mock's true effect must be found) and the same command with `--url` pointed at `python -m mycelium.cli sim-teacher` (HTTP path, token counts).

**Acceptance Scenarios**:

1. **Given** a model where hints raise accuracy, **When** the kill test runs, **Then** the verdict is `pays` and the `same − none` accuracy interval lies above 0.
2. **Given** a model where hints change nothing, **When** the kill test runs, **Then** the verdict is `kill`.
3. **Given** a model that answers worse with hints, **When** the kill test runs, **Then** the verdict is `kill`, even if it uses fewer tokens.
4. **Given** too few problems to tell, **When** the intervals straddle the thresholds, **Then** the verdict is `inconclusive` and the owner runs more templates.

---

### User Story 2 - Turn the measured effect into economics (Priority: P2)

The report also gives the mock parameters (`hint_gain`, `procedural_transfer`) that reproduce the measured accuracies. The owner feeds them to `python -m mycelium.cli insights` to see what memory would save at that effect size.

**Why this priority**: A verdict says whether hints help; the economics say whether the help is worth building memory for.

**Independent Test**: Run the kill test on the mock with a known `hint_gain`; the fitted 95% interval must contain it (`tests/test_killtest.py`).

**Acceptance Scenarios**:

1. **Given** a mock student with `hint_gain` 0.4 and transfer 0.25, **When** the kill test runs on 30 templates × 10 variants, **Then** the fitted `hint_gain` interval contains 0.4.

---

### User Story 3 - Resume a long run (Priority: P3)

A 1,500-call run on a GPU can be interrupted (power, crash, server restart). With `--trials`, finished trials are appended to a JSON-lines file and a rerun skips them.

**Why this priority**: Saves hours of GPU time; not needed for correctness.

**Independent Test**: Run twice with the same `--trials` file; the second run makes no model calls (`tests/test_killtest.py`).

**Acceptance Scenarios**:

1. **Given** a finished trials file, **When** the same command reruns, **Then** no requests reach the model and the report is identical.

### Edge Cases

- A template whose step-count family has no other template: the `other` donor falls back to any other template (never happens with the committed data; a test checks all 100).
- The model prints no number: JUDGE counts it wrong.
- The server returns no token count: `OpenAICompatBackend` estimates tokens as characters / 4.
- Accuracy without hints is already near 0 or 1: no room to move, so the verdict tends to `kill` or `inconclusive`; pick a model or variant set in the 30–90% range.
- A server error mid-run: the run stops with `BackendError`; rerun with the same `--trials` file to continue.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The test MUST use the committed GSM-Symbolic file unchanged: variant 0 of each template donates the insight, variants 1..K are targets.
- **FR-002**: Every target MUST be solved under three conditions: `none`, `same` (insight from its own template), `other` (insight from a different template of the same step-count family).
- **FR-003**: The insight MUST be the donor question plus its verified reference solution, passed through the same `Hint` path the pipeline uses.
- **FR-004**: Decoding MUST be deterministic (temperature 0, as in the GSM-Symbolic paper's protocol); the token cap MUST be configurable.
- **FR-005**: Correctness MUST come from JUDGE (`judge_math`: last number in the answer equals the reference).
- **FR-006**: Differences MUST be paired per target, with 95% intervals from a bootstrap over templates, because variants of one template are correlated.
- **FR-007**: The verdict rule MUST be the one in `research.md`, fixed before any real run. Changing it needs a `docs/decisions.md` entry first, never after seeing results.
- **FR-008**: The report MUST include the mock parameters that reproduce the measured accuracies, with an interval for `hint_gain`.
- **FR-009**: With `--trials`, finished trials MUST be appended as they complete and skipped on rerun.
- **FR-010**: The harness MUST run in CI against the mock and the simulated teacher, with no GPU.
- **FR-011**: GSM-Symbolic MUST NOT be used for training; its canary string stays in place.

### Key Entities

- **Template**: one GSM-Symbolic `id` (0–99), its step-count family, and 50 variants.
- **Insight**: the donor variant's question and verified solution, shown to the model as a hint.
- **Trial**: one target solved under one condition: correct or not, effort (tokens, or loops for the mock), donor similarity.
- **Report**: accuracies, effort, paired differences with intervals, mock equivalents, verdict.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On the mock with a known `hint_gain`, the fitted 95% interval contains the true value (checked in CI).
- **SC-002**: On the mock with `hint_gain` 0 or negative, the verdict is `kill` (checked in CI).
- **SC-003**: A real run of 50 templates × 10 variants (1,500 calls) completes on the RTX 3090 and produces a verdict. Time is not yet measured; rough estimate 1–2 hours for a ~2B student.
- **SC-004**: The verdict and its numbers are recorded in `docs/decisions.md` in the same PR as the run, and the next HIKMAT task follows from it (continue, rethink or run more).

## Assumptions

- The reference solution stands in for a teacher-verified solution, which is what HIKMAT stores after an escalation. A run with the student's own verified solutions is a follow-up (it needs the raw reply text, which `Answer` doesn't keep).
- The step-count family (short ≤3, medium 4–5, long ≥6 solution lines) is a crude stand-in for "similar problem". Real HIKMAT retrieval uses hidden-state keys (spec 002 T015).
- The similarity printed in the hint comes from the stand-in keys, not from the model.
- The student is the spec 002 student or any instruct model served by an OpenAI-compatible server; results apply to that model only.
