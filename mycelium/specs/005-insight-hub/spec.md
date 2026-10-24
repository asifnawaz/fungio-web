# Feature Specification: Insight-sharing hub

**Feature Branch**: `005-insight-hub`

**Created**: 2026-10-24

**Status**: Draft, blocked. Starts only when spec 003's decisive run says `pays` and spec 002 T016 shows memory lowers cost on real problems. Any server, domain or spending needs the owner's approval (`[OWNER]`).

**Input**: Owner's goal from the design discussions: devices share what they learned so everyone's model gets cheaper and better, for free, without sharing personal data.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Download verified insight packs (Priority: P1)

A device downloads a signed pack of insights that many devices verified independently, checks the signature and the model version, and passes them through its own quarantine and shadow test before use.

**Why this priority**: Receiving is safe to build first: nothing leaves the device.

**Independent Test**: A pack built from simulated devices installs on a fresh device; a tampered or wrong-version pack is rejected.

**Acceptance Scenarios**:

1. **Given** a pack signed with an unknown key, **When** the device loads it, **Then** it is rejected and nothing enters memory.
2. **Given** a valid pack, **When** its insights are installed, **Then** they enter quarantine and only promoted ones are used.

---

### User Story 2 - Contribute insights, opt-in (Priority: P2)

With the user's explicit consent, a device sends only verified, anonymized insights (method text and model version, never the user's question), with differential-privacy noise on anything that could identify the user.

**Independent Test**: An audit script shows no user text in any outgoing payload over a simulated week.

**Acceptance Scenarios**:

1. **Given** consent is off (the default), **When** the device learns insights, **Then** nothing is sent.

---

### User Story 3 - Consensus and re-verification (Priority: P2)

The hub accepts an insight only when enough independent devices proposed it and a server-side JUDGE re-verified it; device reputation drops for rejected submissions.

**Independent Test**: Simulated poisoners (a fraction of devices sending bad insights) never get an insight into a pack.

### Edge Cases

- Coordinated poisoning by many fake devices: consensus thresholds plus reputation plus server-side JUDGE; measured in simulation before launch.
- A model version changes: packs are per version; old packs are ignored.

## Requirements *(mandatory)*

- **FR-001**: Opt-in only; off by default. No user questions, answers or identifiers leave the device.
- **FR-002**: Packs are signed; devices verify signature and model version.
- **FR-003**: Every downloaded insight goes through the device's own quarantine and shadow test (constitution III).
- **FR-004**: Server-side re-verification with deterministic JUDGE; consensus across independent devices.
- **FR-005**: Free infrastructure only (constitution VIII): static hosting for packs, e.g. Hugging Face datasets; no paid servers without the owner's approval.

## Success Criteria *(mandatory)*

- **SC-001**: In simulation with 10% poisoning devices, zero poisoned insights reach a pack.
- **SC-002**: A device that installs packs reaches lower mean cost on real problems than one without, at equal accuracy (measured like spec 002 T016).

## Assumptions

- Needs a legal/privacy review of what "anonymized" means for method text before any real contribution (`[OWNER]`).
- Starts as a simulation in this repo (many simulated devices), like spec 001 did for the pipeline.
