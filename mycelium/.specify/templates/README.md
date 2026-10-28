# Spec Kit templates

Copied from [github/spec-kit](https://github.com/github/spec-kit) `templates/` (main branch, version 1.2.4.dev0, fetched 2026-10-24; MIT License, Copyright GitHub, Inc.). One change: the `__SPECKIT_COMMAND_*__` placeholders that `specify init` fills in are written out as `/speckit.<command>`.

Use them when starting a new feature under `specs/NNN-name/`:

| File | Becomes | Spec Kit command |
|---|---|---|
| `spec-template.md` | `spec.md`: prioritized user stories, acceptance scenarios, FR-/SC- requirements | `/speckit.specify`, `/speckit.clarify` |
| `plan-template.md` | `plan.md`, plus `research.md`, `data-model.md`, `quickstart.md`, `contracts/` | `/speckit.plan` |
| `tasks-template.md` | `tasks.md`: `- [ ] T001 [P] [US1] description with file path`, phases per user story | `/speckit.tasks` |
| `checklist-template.md` | `checklists/*.md` (requirements-quality review, reviewer-owned) | `/speckit.checklist` |
| `constitution-template.md` | `.specify/memory/constitution.md` | `/speckit.constitution` |

Order: constitution → specify → clarify → plan → checklist → tasks → analyze → implement → converge. After implementing, check the code against spec, plan and tasks ("converge") and append any gap as a new task under a "Convergence" heading in `tasks.md`.

The MIT License text is in `LICENSE-spec-kit` next to this file.
