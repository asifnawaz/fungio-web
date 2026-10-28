# Feature Specification: Recursive self-improvement (RSI)

**Feature Branch**: `006-rsi` (developed on `claude/mycelium-mock-pipeline`)

**Created**: 2026-10-24

**Status**: Mock loop done and tested (`python -m mycelium.cli rsi`); real-model kill test pending (needs spec 002 T010)

**Input**: Owner: "Hamain RSI bhi chahye" (we also need RSI). From the design discussions: the model should improve itself without a human babysitting it, and keep learning.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The model trains itself, safely (Priority: P1)

Each generation the model proposes or picks problems with checkable answers, solves them several times, keeps only verified solutions at the edge of its ability, trains a copy of itself on them, and replaces itself only if the copy is better on an exam it never trains on.

**Why this priority**: The autopilot (spec 001) improves memory only. Without this, the weights never get better after distillation.

**Independent Test**: `python -m mycelium.cli rsi` on the mock; `tests/test_rsi.py`.

**Acceptance Scenarios**:

1. **Given** a working verifier, **When** the loop runs, **Then** every promoted generation has an exam gain whose 95% lower bound is above 0 and no rise in hallucination, and the final exam accuracy is above the start.
2. **Given** a verifier that keeps only wrong traces, **When** the loop runs, **Then** nothing is promoted and the model ends exactly as it started.
3. **Given** a broken verifier that keeps everything, **When** the loop runs, **Then** the exam accuracy never ends below the start.

---

### User Story 2 - It stops on its own (Priority: P1)

The loop stops after a run of generations without a promotion (plateau), or when its own problems keep improving while the exam doesn't (Goodhart: it is learning to pass its own tests).

**Why this priority**: A self-improving loop that doesn't know when to stop wastes compute or drifts.

**Independent Test**: `tests/test_rsi.py` (plateau with an inverted verifier; Goodhart with a proposer that can't reach the exam's domain).

**Acceptance Scenarios**:

1. **Given** an exam of code problems and a proposer that only makes math, **When** self-made problems improve, **Then** the loop stops with `goodhart` and promotes nothing.

---

### User Story 3 - It improves how it improves (Priority: P2)

The loop keeps several recipes (difficulty band, breadth of families) and picks the next one by the exam gain each produced (a UCB bandit). That is the recursive part: the improver is improved by measured results. The judges, the golden set, the exam and the gates are outside its reach.

**Independent Test**: bandit test in `tests/test_rsi.py`; recipe statistics in the report.

**Acceptance Scenarios**:

1. **Given** one recipe that produced a gain and others that didn't, **When** the bandit has tried each once, **Then** it picks the one with the gain.

---

### User Story 4 - Real model kill test (Priority: P1, needs the GPU PC)

Two STaR-style generations on the real student: GSM8K *train* questions (answers known), verified self-solutions at the frontier, LoRA SFT, exam on held-out GSM8K test + MATH-500 samples + golden set. Verdict rules are fixed in `research.md` before the run.

**Independent Test**: the report and verdict in `research.md`.

### Edge Cases

- Proposed problems overlap the exam: the loop raises an error (it must never train on its exam).
- The golden set is altered: `TamperError` on the next read.
- No problem falls in the recipe's band: the generation trains on the anchor only and is judged like any other.
- Facts (QA, MCQ): excluded from self-training, because a self-made fact question has no source to verify the answer against.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Self-training data MUST come only from verifiable domains (math, code) and only from traces JUDGE verifies.
- **FR-002**: Each generation MUST train a copy; the live model changes only on promotion.
- **FR-003**: Promotion MUST require the paired-bootstrap 95% lower bound of the exam accuracy gain to be above 0 and hallucination not to rise by more than 0.01.
- **FR-004**: The exam (golden set + held-out problems) MUST be disjoint from anything the loop trains on; the golden set stays fingerprinted.
- **FR-005**: The loop MUST stop on a plateau (`patience` generations without promotion) and on Goodhart (`goodhart_strikes` generations in a row with self-gain > 0.02 and exam gain ≤ 0).
- **FR-006**: Each promotion MUST change the model `version`, so HIKMAT drops insights from older weights.
- **FR-007**: A share of verified teacher traces (the anchor) MUST be mixed into every generation, against drift.
- **FR-008**: The recipe choice MUST be driven only by measured exam gains.
- **FR-009**: The loop MUST NOT be able to modify JUDGE, the golden set, the exam or the gate thresholds (constitution IV).

### Key Entities

- **Recipe**: difficulty band + breadth; scored by exam gain.
- **Generation**: proposals, kept problems, verified traces, candidate, exam gain with lower bound, self gain, promotion, version.
- **Exam**: golden set + held-out problems; never trained on.

## Success Criteria *(mandatory)*

- **SC-001**: On the mock, all acceptance scenarios hold in CI.
- **SC-002**: On the real student, the pre-registered verdict for two generations is recorded (`research.md`), with the hardware and commands.

## Assumptions

- The mock's learning rule (`MockModel.learn_self_play`: most learning at a 50% success rate, wrong traces harm, untrained families fade) is an assumption to exercise the gates. It says nothing about whether real self-training helps; US4 does.
- The first real round uses GSM8K train questions with known answers (STaR). Fully self-proposed problems, where the model writes a problem and a program that computes its answer (as in Absolute Zero), come after a `pays` verdict.
