# Plan 001: v0.1 pipeline

## Architecture
```
Problem ─► TRIAGE ─► HIKMAT lookup (hint?) ─► student.answer(stop_at=emit)
              │            confident? ─► emit / retrieve
              │            medium?    ─► think (k attempts, confidence-weighted vote)
              │            low?       ─► teacher (cached) ─► escalate / abstain
              ▼
      verified long solves ─► HIKMAT.propose ─► quarantine
                                   │
     end of day: Autopilot.review (shadow test) ─► promote / reject
                 Autopilot.check_health (golden set) ─► keep / rollback
```

## Interfaces
- `ModelBackend.answer(problem, *, max_loops, hint=None, sample=0, stop_at=None) -> Answer`
- `TrainableBackend.learn_sft(records)`, `learn_rlcr(samples)`
- `VectorIndex.add / remove / search(vector, k)`

## Key choices
- Lookup before reasoning: it costs ~0.1 of a loop.
- The router passes `stop_at` so the model keeps thinking until the router's bar is met.
- Teacher cost per loop = 16× the student's (27B vs ~1.7B parameters).
- Record ids only increase across rollbacks, so audit logs stay unambiguous.
- `numpy` index by default; `binary-ivf` (XOR + IVF) beyond ~100k records.
