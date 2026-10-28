# Quickstart: run the kill test

## 1. Check the harness (any machine, ~10 s)

```bash
cd mycelium
python -m mycelium.cli killtest --mock
```

The mock's hints help by construction, so expect `verdict: pays` and a fitted `hint_gain` interval that contains 0.4 (the mock default).

## 2. Run it on a real model (GPU PC)

Serve the student with any OpenAI-compatible server. With llama.cpp:

```bash
llama-server -m models/<student>.gguf -ngl 99 -c 16384 -np 4 --reasoning off --port 8081   # add --spec-type draft-mtp for an MTP build
python -m mycelium.cli killtest --url http://localhost:8081 --model student --workers 4 \
    --templates 50 --variants 10 --trials killtest-trials.jsonl --out killtest-report.json
```

- First reading (T010a): the untrained `Qwen3.5-2B-Q8_0.gguf` (done, runs 1–2). Since 2026-10-28 the student is `LiquidAI/LFM3-1.7B`: repeat the first reading on `LFM3-1.7B-Q8_0.gguf` from `LiquidAI/LFM3-1.7B-GGUF` (T010a', add `--jinja`, needs llama.cpp with PR #31252 / commit `19cce69` or newer). Decisive run (T010b): the trained spec 002 student.
- Before the full run, send one request with `curl` and read the raw reply. If it has no `ANSWER:` line (cut off, or long thinking text), raise `--max-tokens` or switch the model to non-thinking mode as its model card describes; don't guess the switch.
- Pick a model whose accuracy without hints is roughly 30–90% on these problems, so there is room to move in both directions.
- If the run stops, run the same command again; `--trials` resumes it.
- `inconclusive`: rerun with `--templates 100` (trials already in the file are reused where templates overlap).

## 3. Record the result

1. Paste the printed report and the command, model file and hardware into `specs/003-insight-kill-test/research.md` under a new "Real runs" heading.
2. Add the verdict to `docs/decisions.md` → "Do insights work?".
3. Price the effect: `python -m mycelium.cli insights --suite symbolic --gain <fitted hint_gain> --transfer <fitted transfer>`.
4. Follow the verdict's next step in `research.md` (continue, rethink, or run more).

Never train on GSM-Symbolic: its rows carry Apple's canary string so contamination can be detected.
