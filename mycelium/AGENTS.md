# AGENTS.md: start here

Context for any AI coding agent (Claude Code, Codex, Cursor, Aider) working on MYCELIUM. Read this file, then `.specify/memory/constitution.md`, then the spec you are working on under `specs/`.

## What this project is

MYCELIUM is a small language model system that:
1. is **honest about uncertainty** (RLCR calibration, abstains instead of guessing),
2. **gets cheaper the more it is used** (HIKMAT memory turns verified, expensive solutions into reusable hints),
3. **improves itself without a human babysitting it** (autopilot: quarantine → shadow test → promote, with automatic rollback),
4. runs on modest hardware (target: one RTX 3090 24 GB + 32 GB RAM, later phones).

The project is free and open source, and will stay that way (intended license: AGPL-3.0-or-later). The owner is Asif. He writes in Roman Urdu and English, and prefers replies in Roman Urdu that start with "Asif".

## Status

- **Done (spec 001):** full v0.1 pipeline on a mock student, with a mock or real HTTP teacher. 58 tests. See `specs/001-v0.1-pipeline/`.
- **Next (spec 002):** real models on the owner's GPU PC. See `specs/002-real-models/tasks.md` and pick the first unchecked task.
- **Research track (not scheduled):** see `docs/decisions.md` → "Research track".

## Layout

```
mycelium/
  AGENTS.md                 this file
  CLAUDE.md                 points Claude Code here
  .specify/memory/constitution.md   non-negotiable rules
  specs/NNN-*/              spec.md, plan.md, research.md, tasks.md per feature
  docs/decisions.md         decisions, rejected options, measured numbers
  mycelium/
    types.py                Problem, Answer, Hint
    evals/                  datasets (synthetic), judges (JUDGE), metrics, harness
    models/                 base protocols, mock, openai_compat (real servers), cache
    distill.py rlcr.py router.py autopilot.py pipeline.py
    hikmat/                 codec (2-bit CODON), index (numpy, faiss-hnsw, binary-ivf), memory
    sim_teacher.py          simulated teacher on an OpenAI-compatible HTTP endpoint
    bench.py cli.py
  tests/                    pytest, one file per module + end-to-end
```

## Commands

```bash
cd mycelium
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev,faiss]"
pytest -q                                           # must stay green
ruff check --select F,E9,B --ignore B008 --line-length 120 mycelium tests
python -m mycelium.cli e2e --out report.json        # mock teacher
python -m mycelium.cli sim-teacher --port 8080 &    # simulated HTTP teacher
python -m mycelium.cli e2e --teacher-url http://localhost:8080 --teacher-model sim-qwen
python -m mycelium.cli bench --n 1000000            # HIKMAT index speeds
```

Real teacher on the GPU PC: see README → "With a real teacher".

## How to work here

- Pick one task from the active `tasks.md`. Do it, tick it, and note anything learned in that spec's `research.md` or in `docs/decisions.md`.
- Write or update the test first, then the code. A task is done when `pytest -q` and the ruff command pass.
- Keep changes small and in the style of the surrounding code: type hints, short docstrings that say *why*, no dead code.
- New behavior that touches a real model must also work with the mock and the simulated teacher, so CI never needs a GPU.
- Measure before claiming a speedup. Put the numbers, the hardware and the command in the README or `docs/decisions.md`.
- Report honestly. If something is slower, worse or unverified, say so; a measured negative result is worth keeping (see the XOR-in-NumPy note in `docs/decisions.md`).

## Hard rules (see the constitution for all of them)

- Never weaken, skip or delete a test, JUDGE, or the golden set to make something pass.
- The model under test never grades itself. JUDGE is deterministic code.
- Never put API keys or tokens in code, commits, logs or command lines. Read them from environment variables (`--teacher-api-key-env`).
- Never let the autopilot modify its own judges, golden set or health limits.
- Personal user data never leaves the device; only verified, anonymized insights may be shared.
