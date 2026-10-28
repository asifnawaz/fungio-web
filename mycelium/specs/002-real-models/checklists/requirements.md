# Specification Quality Checklist: Real models on one GPU

**Purpose**: Check that spec.md is complete and testable before building on it
**Created**: 2026-10-24
**Feature**: [spec.md](../spec.md)

## Content quality

- [x] Says what the owner gets and why (real teacher, honest student, memory only on evidence)
- [x] Mandatory sections filled (user scenarios, requirements, success criteria)
- [x] Tool choices kept in plan.md, except where they are the requirement (teacher model, TRL + one kernel library)

## Requirement completeness

- [x] No `[NEEDS CLARIFICATION]` markers remain
- [x] Requirements FR-001–FR-008 are testable and map to tasks
- [x] Success criteria are measurable (SC-001–SC-004)
- [x] Edge cases listed (format drift, VRAM, tokenizer mismatch, inconclusive kill test)
- [x] Scope bounded; out-of-scope items named in Assumptions
- [x] Student model chosen by name (`LiquidAI/LFM3-1.7B` since 2026-10-28, earlier `Qwen/Qwen3.5-2B`; see `specs/ROADMAP.md`)
- [ ] Student/teacher token ids confirmed identical (T010's first check)

## Feature readiness

- [x] Each user story has an independent test and acceptance scenarios
- [x] Memory work is gated on the spec 003 verdict

## Notes

- Reviewed by the implementing agent on 2026-10-24; the owner may re-review and untick anything.
