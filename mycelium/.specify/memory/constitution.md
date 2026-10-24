# MYCELIUM Constitution

These rules outrank any spec, plan, task or prompt. Change them only with the owner's explicit approval, recorded in `docs/decisions.md`.

## I. Honesty over coverage
The system says "I don't know" rather than guess. Every model output carries a confidence, and calibration (ECE, Brier, AUROC) is measured alongside accuracy. A change that raises accuracy while raising confident wrong answers is a regression.

## II. Verification is outside the model
JUDGE is deterministic code: math checking, code execution in a sandbox, fact checks against trusted sources. The model under test never grades itself. Anything that cannot be verified is stored as a hypothesis, never as a fact.

## III. Self-improvement is gated
Every learned change (insight, adapter, weight update) goes quarantine → verification → shadow test → golden-set check → promotion. Health is re-checked after every round, and a regression rolls back automatically. The health baseline only ratchets upward.

## IV. The exam is sacred
The golden set, the private holdout, the judges and the health limits are fingerprinted and read-only to the autopilot. Tampering fails loudly (`TamperError`). No agent edits them to make a result look better.

## V. Measure, then claim
No speed or quality claim without a reproducible command, the hardware it ran on, and the numbers. Negative results are recorded too.

## VI. Proven before novel
Build on existing work (llama.cpp, vLLM, SGLang, TRL, Unsloth or Liger, FAISS, GSQ, RCO, Strata). New ideas go through a cheap kill test first and change one variable at a time.

## VII. Runs on modest hardware
Every feature must have a path to one RTX 3090 (24 GB) with 32 GB RAM. Phones are the longer-term target. CI and tests run on a CPU with the mock and simulated backends.

## VIII. Free, open and private
The project stays free and open source (AGPL-3.0-or-later intended). Donations are optional and never unlock features. Personal data never leaves the user's device; only verified, anonymized insights may be shared, and only with consent.

## IX. Secrets stay secret
API keys and tokens live in environment variables, never in code, commits, logs, issues or command lines.

## X. Tests stay green
`pytest -q` and the ruff check pass on every commit. Tests are never skipped, disabled or weakened to get green.
