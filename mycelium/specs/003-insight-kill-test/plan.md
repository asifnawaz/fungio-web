# Implementation Plan: HIKMAT kill test on GSM-Symbolic

**Branch**: `003-insight-kill-test` (on `claude/mycelium-mock-pipeline`) | **Date**: 2026-10-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-insight-kill-test/spec.md`

## Summary

Measure, on a real model, whether a remembered verified solution helps on a new variant of the same problem, before building more of HIKMAT. GSM-Symbolic's templates give controlled pairs: same reasoning, new names and numbers. One module (`mycelium/killtest.py`) plans and runs the trials through any `ModelBackend`, analyzes them with a template-level bootstrap, applies a pre-registered verdict, and fits the mock parameters that reproduce the result so `insights` can price it.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: NumPy; standard library `urllib` for HTTP (through `OpenAICompatBackend`). No new dependency.

**Storage**: Trials as JSON lines (`--trials`), report as JSON (`--out`).

**Testing**: pytest (`tests/test_killtest.py`), ruff (`F,E9,B`).

**Target Platform**: CPU container for CI (mock, simulated teacher); owner's PC (RTX 3090 24 GB, 32 GB RAM) with `llama-server` for the real run.

**Project Type**: Library module plus a CLI subcommand in the existing `mycelium` package.

**Performance Goals**: Mock run with the calibration fit under 15 s at 50 × 10 (measured 9.5 s). Real run time is set by the model server.

**Constraints**: No GPU in CI; GSM-Symbolic is evaluation-only; keys only from environment variables.

**Scale/Scope**: Up to 100 templates × 49 variants × 3 conditions = 14,700 calls; default 1,500.

## Constitution Check

*GATE: checked before research and again after design.*

| Principle | How this feature complies |
|---|---|
| I. Honesty over coverage | Reports intervals and an `inconclusive` outcome instead of forcing a yes or no. |
| II. Verification outside the model | Correctness from `judge_math`; the model never grades itself. |
| III. Gated self-improvement | Not touched: the test learns nothing and changes no memory. |
| IV. The exam is sacred | GSM-Symbolic file is SHA-256 checked; the verdict rule is fixed in `research.md` before real runs. |
| V. Measure, then claim | Every number in `research.md` comes from a command run on stated hardware. |
| VI. Proven before novel | This is the kill test the constitution asks for before HIKMAT work continues. |
| VII. Modest hardware | Runs on CPU with the mock; real run on one 3090. |
| VIII. Free, open, private | No user data involved. |
| IX. Secrets | `--api-key-env` reads the key from the environment. |
| X. Tests stay green | `tests/test_killtest.py` added; full suite passes. |

No violations.

## Project Structure

### Documentation (this feature)

```text
specs/003-insight-kill-test/
├── spec.md
├── plan.md               # this file
├── research.md           # pre-registered rules, harness checks, related work
├── data-model.md
├── quickstart.md         # how to run it on the GPU PC
├── contracts/
│   ├── cli.md            # killtest command contract
│   └── report.schema.json
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code

```text
mycelium/
├── mycelium/
│   ├── killtest.py               # plan, run, analyze, fit_mock, verdict, format_report
│   ├── cli.py                    # `killtest` subcommand
│   ├── evals/real.py             # read_gsm_symbolic_rows, load_gsm_symbolic
│   ├── models/openai_compat.py   # Answer.tokens from the server's usage field
│   └── types.py                  # Answer.tokens
└── tests/
    └── test_killtest.py
```

**Structure Decision**: One module inside the existing package; it reuses `Problem`, `Hint`, `judge`, `OpenAICompatBackend` and the mock instead of adding a parallel harness.

## Complexity Tracking

None.
