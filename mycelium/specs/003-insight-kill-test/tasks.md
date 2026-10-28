---
description: "Tasks for the HIKMAT kill test on GSM-Symbolic"
---

# Tasks: HIKMAT kill test on GSM-Symbolic

**Input**: `specs/003-insight-kill-test/` (spec.md, plan.md, research.md, data-model.md, contracts/)

**Tests**: Required (constitution X). Each story's tests are listed with it.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- **[Story]**: US1, US2, US3 from spec.md
- Paths are relative to `mycelium/`

## Phase 1: Setup

- [x] T001 Commit GSM-Symbolic verbatim with Apple's notice and a SHA-256 test (`mycelium/data/samples/gsm_symbolic.jsonl`, `LICENSE-gsm-symbolic.txt`, `tests/test_real_data.py`)
- [x] T002 [P] Add `read_gsm_symbolic_rows` (raw rows incl. reference solution) next to `load_gsm_symbolic` in `mycelium/evals/real.py`

## Phase 2: Foundational

- [x] T003 Add `Answer.tokens` and fill it from the server's `usage.completion_tokens` in `mycelium/types.py`, `mycelium/models/openai_compat.py`
- [x] T004 Write the pre-registered hypotheses and verdict rules in `specs/003-insight-kill-test/research.md` before any real run

**Checkpoint**: data, token counts and decision rules exist.

## Phase 3: User Story 1 - Verdict on whether a stored method helps (Priority: P1) 🎯 MVP

**Goal**: one command gives accuracy and tokens per condition, paired intervals and a verdict.

**Independent Test**: `python -m mycelium.cli killtest --mock` → `pays`; same against `sim-teacher` over HTTP completes with token counts.

- [x] T005 [P] [US1] Tests: other donor is a different template of the same family; known effect → `pays`; zero or negative effect → `kill`; verdict table for all three outcomes; HTTP run against the simulated teacher (`tests/test_killtest.py`)
- [x] T006 [US1] Trial planning and execution: donors, three conditions, `Hint` with the donor solution (`mycelium/killtest.py: load_items, choose_templates, other_donor, run`)
- [x] T007 [US1] Analysis: paired differences, bootstrap over templates, verdict, text report (`mycelium/killtest.py: analyze, verdict, format_report`)
- [x] T008 [US1] CLI subcommand `killtest` with `--url/--mock`, `--api-key-env`, sizes, `--out` (`mycelium/cli.py`)
- [x] T009 [US1] Report contract and a test that the report matches it (`contracts/report.schema.json`, `tests/test_killtest.py`)
- [ ] T010a [US1] **First reading** with the untrained student, right after its baseline (spec 002 T001b, same server on port 8081): `python -m mycelium.cli killtest --url http://localhost:8081 --model qwen3.5-2b --workers 4 --templates 50 --variants 10 --trials reports/killtest-base.jsonl --out reports/killtest-base.json`.
  Proof: report, command, model file and hardware under "Real runs" in `research.md`, labeled "base Qwen3.5-2B, untrained"; verdict in `docs/decisions.md`. Gate: `specs/ROADMAP.md` row 3.
- [ ] T010a' [US1] **First reading on the new student** `LiquidAI/LFM3-1.7B` (decision 2026-10-28), right after its baseline (spec 002 T001c): the T010a command with `--model lfm3-1.7b`, `--trials reports/killtest-lfm3.jsonl --out reports/killtest-lfm3.json`. Same frozen verdict rule.
  Proof: as T010a, labeled "base LFM3-1.7B, untrained". Gate: `specs/ROADMAP.md` row 3b.
- [ ] T010b [US1] **Decisive run** with the trained student (after spec 002 T013), same command with its server and `--trials reports/killtest-trained.jsonl`. This is spec 002 T015a.
  Proof: as T010a, labeled with the student's `version`. Gate: `specs/ROADMAP.md` row 16.

**Checkpoint**: the verdict decides whether spec 002 T015–T016 go ahead.

## Phase 4: User Story 2 - Turn the effect into economics (Priority: P2)

**Goal**: mock parameters that reproduce the measured accuracies, ready for `insights`.

**Independent Test**: on the mock with a known `hint_gain`, the fitted interval contains it.

- [x] T011 [P] [US2] Test: fitted `hint_gain` interval contains the true 0.4 (`tests/test_killtest.py`)
- [x] T012 [US2] Calibration fit by bisection on the measured problems, averaged over 5 mock seeds, matching differences (`mycelium/killtest.py: fit_mock`); record the two rejected estimators in `research.md`
- [ ] T013 [US2] After T010b: run `insights --suite symbolic` with the fitted values and add the row to `research.md`

## Phase 5: User Story 3 - Resume a long run (Priority: P3)

**Goal**: an interrupted run continues without repeating calls.

**Independent Test**: second run with the same `--trials` makes zero model calls.

- [x] T014 [P] [US3] Test: rerun makes no calls and returns identical trials (`tests/test_killtest.py`)
- [x] T015 [US3] Append trials as JSON lines and skip finished keys (`mycelium/killtest.py: run`)

## Phase 6: Polish & Cross-Cutting

- [x] T016 [P] Docs: README, AGENTS.md, `docs/decisions.md`, spec 002 T015a points here
- [ ] T017 Follow-up: insights from the student's *own* verified solutions (needs the raw reply text kept on `Answer`)
- [ ] T018 Follow-up: GSM-Symbolic P1/P2 (one or two extra clauses) as harder targets; fetch with `scripts/fetch_datasets.py --gsm-symbolic`
- [ ] T019 Follow-up: retrieve the donor by real hidden-state similarity instead of fixed template pairs, once spec 002 T015 exists

## Dependencies & Execution Order

- Setup → Foundational → US1. US2 and US3 build on US1's `run`/`analyze` but are tested independently.
- T010a needs spec 002 T001b (student server running). T010b needs spec 002 T013. T013 needs T010b.
- T017–T019 come after a `pays` or `inconclusive` verdict; after `kill` they are dropped.

## Implementation Strategy

US1 alone answers the owner's question. US2 makes the answer actionable. US3 only saves GPU time.

## Convergence

Checked against spec.md on 2026-10-24: FR-001–FR-011 are covered by T001–T015 except the real runs (T010a, T010b; SC-003, SC-004), which needs the GPU PC.
