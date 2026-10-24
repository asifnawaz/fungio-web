# Contract: `python -m mycelium.cli killtest`

```text
python -m mycelium.cli killtest (--url URL | --mock)
    [--model NAME] [--api-key-env VAR]
    [--templates N] [--variants K] [--max-tokens T]
    [--seed S] [--trials PATH] [--out PATH]
```

| Flag | Default | Meaning |
|---|---|---|
| `--url` | — | OpenAI-compatible server of the model under test (`/v1/chat/completions`) |
| `--mock` | — | the mock student; checks the harness, says nothing about real models |
| `--model` | `student` | model name sent to the server |
| `--api-key-env` | none | name of the environment variable holding the key; the key never goes on the command line |
| `--templates` | 50 | templates sampled (seeded) from 100 |
| `--variants` | 10 | target variants per template (1–49) |
| `--max-tokens` | 2048 | cap on each reply |
| `--seed` | 0 | template sample, `other` donors and bootstrap |
| `--trials` | none | JSON-lines file; finished trials are appended, a rerun resumes |
| `--out` | none | report JSON, shape in `report.schema.json` |

**Requests.** One chat completion per trial: system prompt asking for `ANSWER:` and `CONFIDENCE:` lines, the target question, and for `same`/`other` a second user message `A verified approach for a similar problem (similarity 0.xx): Problem: … Verified solution: …`. Temperature 0, `max_tokens` = `--max-tokens`.

**Output.** Progress every 50 trials, then:

```text
templates 50, targets 500 (each solved 3 ways)
condition accuracy    mean tokens
none          …              …
same          …              …
other         …              …
same - none: accuracy +x [lo, hi], tokens +y% [lo, hi]
other - none: accuracy +x [lo, hi], tokens +y% [lo, hi]
mock equivalents: hint_gain g [lo, hi], procedural_transfer t
verdict: pays | kill | inconclusive
```

**Exit codes.** 0 on success; 2 for bad arguments (argparse); a server failure raises `BackendError` with a non-zero exit, and the `--trials` file keeps everything finished so far.
