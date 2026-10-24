# Implementation Plan: Recursive self-improvement (RSI)

**Branch**: `006-rsi` (on `claude/mycelium-mock-pipeline`) | **Date**: 2026-10-24 | **Spec**: [spec.md](spec.md)

## Summary

A generation loop around the existing pieces: the proposer makes verifiable problems, the model's own attempts estimate its success rate, JUDGE keeps verified traces at the frontier, a copy of the model trains on them (plus a teacher anchor), and the copy replaces the model only on a statistically clear exam gain without more hallucination. A UCB bandit over recipes improves the loop's own method from measured gains. Mock first (done), then the real student through `HFStudent.learn_sft`.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: NumPy (mock); for the real run, the spec 002 student stack (transformers, PEFT, TRL)

**Storage**: report JSON (`--out`); real run: LoRA adapters per generation under `checkpoints/rsi-<g>/`

**Testing**: `tests/test_rsi.py` (CPU, ~40 s)

**Target Platform**: CPU for the mock; RTX 3090 for the real kill test

**Project Type**: module `mycelium/rsi.py` + CLI `rsi`

**Performance Goals**: mock run of 8 generations under 1 minute (measured ~36 s)

**Constraints**: the loop never reads or writes JUDGE code, the golden set's contents or the gate thresholds; one model copy in memory at a time on the GPU (train the copy, evaluate, then keep or drop it)

**Scale/Scope**: real run: 1,000 train questions × 4 attempts per generation, 2 generations for the kill test

## Constitution Check

| Principle | How this feature complies |
|---|---|
| I. Honesty | Promotion also requires no rise in hallucination; ECE reported. |
| II. Verification outside the model | Only JUDGE-verified traces; self-rewarding (model grades itself) rejected. |
| III. Gated self-improvement | Weight updates go copy → exam gate → promote, the same shape as the memory autopilot. |
| IV. The exam is sacred | Golden set fingerprinted; exam disjoint from training (checked); gates not reachable from the loop. |
| V. Measure, then claim | Mock numbers labeled as mock; real verdict pre-registered. |
| VI. Proven before novel | STaR-style loop first (published); Absolute Zero-style proposing only after a `pays`. |
| VII. Modest hardware | LoRA on a 2B student fits the 3090. |
| X. Tests stay green | `tests/test_rsi.py`. |

No violations.

## Project Structure

```text
specs/006-rsi/  spec.md  plan.md  research.md  quickstart.md  tasks.md  checklists/requirements.md

mycelium/mycelium/
├── rsi.py              # RSIConfig, Recipe, RSILoop, run_rsi, format_rsi
├── models/mock.py      # MockModel.learn_self_play (the mock's self-training rule)
└── cli.py              # `rsi` subcommand
mycelium/tests/test_rsi.py
```

**Structure Decision**: `RSILoop` talks to the model only through `answer`, `learn_self_play`/`learn_sft` and `version`, so the real student plugs in with an adapter that maps `learn_self_play` to `HFStudent.learn_sft` (task T009).

## Complexity Tracking

None.
