# Research: recursive self-improvement

## Pre-registration for the real kill test (written 2026-10-24, before any real run)

**Setup.** Student: `HFStudent` (spec 002 T010) for `Qwen/Qwen3.5-2B`, first the base model, later the trained one. Problems: 1,000 GSM8K *train* questions (answers known; JUDGE = `judge_math`). Per question 4 attempts at temperature 0.7; keep questions with 1–3 correct (success rate 0.25–0.75, the "frontier" recipe); keep only verified traces; add 200 verified teacher traces as the anchor when the teacher is available. One LoRA SFT epoch per generation. Exam: 300 GSM8K *test* questions not in the committed sample + 100 MATH-500 problems + the golden set; never trained on.

**Measures.** Paired exam accuracy gain per generation, 95% lower bound by bootstrap over exam problems; hallucination rate; ECE.

**Verdict after two generations.**
- `pays`: generation 1's lower bound > 0, generation 2's lower bound > 0, hallucination not up by more than 0.01 in either. Recursion helps at least twice; continue with fully self-proposed problems (`tasks.md` T012).
- `plateau`: generation 1's lower bound > 0, generation 2's not. One round helps, recursion doesn't yet; record, try the other recipes before scaling.
- `kill`: generation 1's lower bound ≤ 0. Self-training doesn't help this model on this data; stop RSI work and record it. Ask the owner (roadmap Q5).

Changing these rules needs a dated entry in `docs/decisions.md` and a fresh run.

## Mock results (4-core Xeon container, `python -m mycelium.cli rsi`, seed 0)

| Setting | Promoted generations | Exam accuracy | Hallucination | Stop |
|---|---|---|---|---|
| verifier on (`judge`), 8 generations | 4 of 8 (frontier, easy, frontier, easy) | 0.778 → 0.972 | 0.222 → 0.028 | budget |
| inverted verifier (keeps only wrong traces), 5 generations | 0 | 0.778 → 0.778 | unchanged | plateau after 3 |
| verifier off (keeps everything), 5 generations | 2 of 5 (both "easy": ~9% wrong traces); the frontier and hard rounds (38% and 56% wrong) were rejected | 0.778 → 0.861 | 0.222 → 0.139 | budget |
| code-only exam, math-only proposer | 0 | — | — | goodhart |

What this shows: the gates do their job (nothing harmful was promoted; the broken-verifier runs never ended worse; the Goodhart stop fires). The size of the gains comes from the mock's learning rule and means nothing about real models.

Observed in the mock: the "easy" recipe (success rate ≥ 0.75) gained as much as "frontier", because it yields many more verified traces per generation. Whether volume or difficulty matters more on a real model is an open question for US4.

## Related work (checked on Hugging Face Papers, 2026-10-24)

- **STaR** (arXiv 2203.14465): iteratively fine-tunes on the model's own rationales that reach the right answer. Our real kill test is one STaR loop with frontier filtering and an exam gate.
- **Absolute Zero** (arXiv 2505.03335): the model proposes and solves its own tasks, verified by a code executor, with no external data. The planned next step after a `pays` verdict.
- **Self-Rewarding Language Models** (arXiv 2401.10020): the model judges its own outputs for iterative DPO. Rejected here: the model must never grade itself (constitution II).
- **Darwin Gödel Machine** (arXiv 2505.22954): an agent that modifies its own code, keeping changes that score better on benchmarks. Our recipe bandit is a small, safe version of "improve the improver": it changes only curriculum settings, never the judges or the exam.
- **Model collapse**: Shumailov et al. 2024 ("AI models collapse when trained on recursively generated data"; see the note arXiv 2410.12954) and "Source Identification Is Not Fitness Testing" (arXiv 2610.00417, recursive training degrades despite provenance filtering). Reason for verification-only traces, the anchor, and the exam gate.
