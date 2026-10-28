---
description: "Tasks for recursive self-improvement (RSI)"
---

# Tasks: Recursive self-improvement (RSI)

**Input**: `specs/006-rsi/` (spec.md, plan.md, research.md). Execution order across specs: `specs/ROADMAP.md`.

**Tests**: Required (constitution X).

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Foundational (mock)

- [x] T001 Mock self-training rule `MockModel.learn_self_play` (frontier learning, harm from wrong traces, forgetting) in `mycelium/models/mock.py`
- [x] T002 Pre-register the real kill test's rules in `research.md`

## Phase 2: User Story 1 - Safe self-training loop (P1)

- [x] T003 [P] [US1] Tests: promotion only on exam gain with lower bound > 0; version per promotion; inverted verifier → no promotion; verifier off → never worse (`tests/test_rsi.py`)
- [x] T004 [US1] `RSILoop`: propose, estimate success rate, frontier filter, verified traces + anchor, train a copy, exam gate (`mycelium/rsi.py`)
- [x] T005 [US1] CLI `python -m mycelium.cli rsi` with `--verify judge|off|inverted` (`mycelium/cli.py`)

## Phase 3: User Story 2 - Stops on its own (P1)

- [x] T006 [P] [US2] Tests: plateau stop; Goodhart stop (code-only exam, math-only proposer); exam overlap refused; golden tampering raises `TamperError`
- [x] T007 [US2] Plateau and Goodhart stops in `RSILoop.run`

## Phase 4: User Story 3 - Improves how it improves (P2)

- [x] T008 [US3] UCB bandit over recipes scored by exam gain, with a test

## Phase 5: User Story 4 - Real kill test (P1, GPU PC)

- [ ] T009 [US4] Adapter so `RSILoop` drives `HFStudent`: `learn_self_play(records)` → `learn_sft(records)` on a copy (load the adapter into a second model or save/restore adapters; one model on the GPU at a time), `version` from the adapter (`mycelium/rsi_real.py`, test with the tiny random model from spec 002 T010). Depends: spec 002 T010.
- [ ] T010 [US4] Fetch 1,000 GSM8K train questions and 300 extra test questions (`python scripts/fetch_datasets.py --split train --subjects` fetches GSM8K train only, since MMLU subjects have no train split; then `--split test --subjects`), plus 100 MATH-500 problems (spec 002 T006).
- [ ] T011 [US4] **Kill test, two generations** with the base student, exactly as `research.md` says. Record the report, commands, hardware and verdict in `research.md`; verdict in `docs/decisions.md`. Gate: roadmap row 11a.
- [ ] T012 [US4] After `pays`: fully self-proposed problems: the model writes a problem plus a Python function that computes its answer; JUDGE runs the function in the sandbox (spec 002 T007) and keeps the problem only if the model's later solution matches. Same gates.
- [ ] T013 [US4] Repeat T011 with the trained student (after spec 002 T013). Gate: roadmap row 16a.

## Dependencies & Execution Order

- Phases 1–4 are done on CPU. T009 needs spec 002 T010; T010 needs network; T011 needs T009–T010 and the GPU; T012 needs T011 = `pays` and the sandbox; T013 needs spec 002 T013.

## Convergence

Checked against spec.md on 2026-10-24: FR-001–FR-009 are covered by T001–T008 on the mock. SC-002 waits on T011.
