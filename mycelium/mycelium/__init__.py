"""MYCELIUM v0.1.

Pipeline for a small, honest model: distillation from a teacher, RLCR calibration,
a confidence router (TRIAGE), HIKMAT memory that turns solved problems into reusable
insights, and an autopilot that only promotes changes that pass automatic checks.

Everything here runs against the `ModelBackend` protocol. The mock backend in
`mycelium.models.mock` lets the whole pipeline run end to end on a CPU; real model
backends plug into the same protocol.
"""

__version__ = "0.1.0"
