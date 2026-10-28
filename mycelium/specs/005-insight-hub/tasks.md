# Tasks: Insight-sharing hub (Draft)

**Blocked until** spec 003 T010b = `pays` and spec 002 T016 is done. Before any task here: write `plan.md` from `.specify/templates/plan-template.md`, then update this list.

## Phase 1: Setup

- [ ] T001 [OWNER] Ask: "The hub needs a place to publish signed insight packs. Is a public Hugging Face dataset under your account OK? No paid servers." Record the answer in `docs/decisions.md`.

## Phase 2: Simulation first (CPU)

- [ ] T002 [US3] Simulate N devices running HIKMAT days, a hub that applies consensus + server-side JUDGE + reputation, and a fraction of poisoning devices (`mycelium/hub_sim.py`, tests).
  Proof: SC-001 holds at 10% poisoners; table of poison rate vs consensus threshold in `research.md`.
- [ ] T003 [US1] Pack format: insights + model version + signature (an existing library, e.g. Ed25519 via a maintained package; choose and justify in `plan.md`), with load-time checks.
  Proof: tests reject a tampered pack and a wrong-version pack.

## Phase 3: User Story 1 - Download packs (P1)

- [ ] T004 [US1] Device-side install: verify, then quarantine and shadow-test every insight (reuse `Autopilot`).

## Phase 4: User Story 2 - Contribute, opt-in (P2)

- [ ] T005 [US2] [OWNER] Privacy review of what an insight payload may contain before any real upload.
- [ ] T006 [US2] Outgoing payload builder with an audit test that no user text leaves the device.

## Phase 5: Measure

- [ ] T007 SC-002 on real problems: device with packs vs without.
