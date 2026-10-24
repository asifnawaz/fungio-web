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
- [ ] Student model chosen by name and its tokenizer match verified (decided in T010)

## Feature readiness

- [x] Each user story has an independent test and acceptance scenarios
- [x] Memory work is gated on the spec 003 verdict

## Notes

- Reviewed by the implementing agent on 2026-10-24; the owner may re-review and untick anything.
