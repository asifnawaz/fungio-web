# Quickstart: RSI

```bash
cd mycelium
python -m mycelium.cli rsi                          # 8 generations on the mock (~40 s)
python -m mycelium.cli rsi --verify inverted        # worst-case verifier: nothing may be promoted
python -m mycelium.cli rsi --verify off             # broken verifier: must never end worse
python -m mycelium.cli rsi --out reports/rsi.json   # full report
```

Reading the table: `exam gain [lo95]` is the candidate's accuracy gain on the exam with the lower end of its 95% interval; a generation is promoted only when that lower end is above 0 and hallucination doesn't rise. `self gain` is the gain on the loop's own problems; when it keeps rising while the exam doesn't, the loop stops with `goodhart`.

Real model: after spec 002 T010 exists, follow `tasks.md` T009–T011. The verdict rules are in `research.md`; don't change them after seeing results.
