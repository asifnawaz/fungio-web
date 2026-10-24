# Spec 001: MYCELIUM v0.1 pipeline (mock backend)

**Status:** Done · **Owner:** Asif · **Constitution:** `.specify/memory/constitution.md`

## Why
Before spending GPU time, prove that every stage of the system works together and that the safety gates fire. That means distillation, calibration, routing, memory and self-improvement, all runnable on a CPU in CI.

## User stories
1. As the owner, I can run one command and see each stage move its metric the right way.
2. As the owner, I can trust that bad self-learned knowledge (poison, tampering) is caught without me watching.
3. As an AI agent, I can swap the mock teacher for a real model server without touching pipeline code.

## Requirements
- R1 A deterministic JUDGE for math, code (subprocess) and QA, where abstaining is correct on unanswerable questions.
- R2 P1 distillation: teacher answers, JUDGE filters, student learns.
- R3 P2 RLCR: reward = correctness − Brier penalty, GRPO-style advantages, a learnable-problem filter, and zero-variance groups dropped.
- R4 P3 TRIAGE: memory lookup → answer / think / escalate / abstain. Thresholds are tuned for minimum cost subject to ≥90% of teacher accuracy and hallucination ≤ teacher + 3 points. The report says `teacher_only` when routing can't beat the teacher.
- R5 HIKMAT memory: 2-bit CODON keys, admission policy, merging, a hard byte budget, value-based eviction, quarantine expiry, versioning, and a fast index.
- R6 Autopilot: quarantine → shadow test → promote/reject, a fingerprinted golden set, a ratcheting health baseline, and rollback.
- R7 Attack tests: a poisoned insight through quarantine (must be rejected), a forced-live poison (must be rolled back), and golden-set tampering (must be detected).
- R8 Real-teacher path: an OpenAI-compatible backend, a response cache, and a simulated HTTP teacher for CI.

## Acceptance (all met, see `tests/test_e2e_mock.py`, `tests/test_sim_teacher.py`)
- Distillation raises student accuracy; RLCR lowers ECE without raising hallucination.
- TRIAGE stays within the teacher's hallucination + 5 points.
- From day 1, HIKMAT days cost less than teacher-only and less than day 0; golden accuracy with memory is above without.
- All three attacks are caught.
- The full pipeline runs through the HTTP teacher.
