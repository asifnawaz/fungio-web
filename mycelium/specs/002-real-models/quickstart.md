# Quickstart: spec 002 on the GPU PC

```bash
git clone <repo> && cd <repo>/mycelium
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev,faiss]"
pytest -q                                          # must pass before anything else

python -m mycelium.cli doctor --network               # what this PC can run

# 1. Small-model baseline first (T001c): the student we train, LFM3-1.7B, 1.85 GB
#    llama.cpp must include PR #31252 (commit 19cce69, 2026-10-27) for lfm3 support
hf download LiquidAI/LFM3-1.7B-GGUF LFM3-1.7B-Q8_0.gguf --local-dir models
llama-server -m models/LFM3-1.7B-Q8_0.gguf -ngl 99 -c 16384 -np 4 --reasoning off --jinja --port 8081
python -m mycelium.cli baseline --url http://localhost:8081 --model lfm3-1.7b --suite real --workers 4 --out reports/baseline-real.json
python -m mycelium.cli baseline --url http://localhost:8081 --model lfm3-1.7b --suite symbolic --workers 4 --out reports/baseline-symbolic.json
python -m mycelium.cli killtest --url http://localhost:8081 --model lfm3-1.7b --workers 4 \
    --trials reports/killtest-base.jsonl --out reports/killtest-base.json   # spec 003 T010a'

# 2. Side-by-side on the GPU (T001d): see the section below

# 3. Teacher (T002-T003)
hf download ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF Qwen3.8-27B-GSQ-RCO-IQ3_S.gguf --local-dir models
llama-server -m models/Qwen3.8-27B-GSQ-RCO-IQ3_S.gguf -ngl 99 -c 32768 --port 8080

# 4. Real-teacher run (T004)
python -m mycelium.cli e2e --teacher-url http://localhost:8080 --teacher-model qwen3.8-27b \
    --suite symbolic --out reports/real-teacher.json
```

## Side-by-side on the GPU (T001d)

Both students on this PC, one server at a time, same questions as the cloud CPU runs. The
evaluation sets come from `python scripts/fetch_datasets.py --evals` (needs `pip install datasets`;
writes `data/full/`). llama.cpp must include PR #31252 (commit `19cce69`, 2026-10-27) for LFM3;
on Windows take a CUDA release published after that date. Never run both servers on 8081 at once.

```bash
pip install datasets && python scripts/fetch_datasets.py --evals
hf download unsloth/Qwen3.5-2B-MTP-GGUF Qwen3.5-2B-Q8_0.gguf --local-dir models
hf download LiquidAI/LFM3-1.7B-GGUF LFM3-1.7B-Q8_0.gguf --local-dir models

# Qwen3.5-2B (MTP speculative decoding)
llama-server -m models/Qwen3.5-2B-Q8_0.gguf -ngl 99 -c 16384 -np 4 --reasoning off --spec-type draft-mtp --port 8081
# in a second terminal set M (bash: M=qwen3.5-2b   PowerShell: $M = "qwen3.5-2b"), then:
python -m mycelium.cli baseline --url http://localhost:8081 --model $M --suite real --workers 4 --out reports/gpu/$M-real.json
python -m mycelium.cli baseline --url http://localhost:8081 --model $M --suite symbolic --workers 4 --out reports/gpu/$M-symbolic.json
python -m mycelium.cli baseline --url http://localhost:8081 --model $M --suite math500 --limit 100 --workers 4 --out reports/gpu/$M-math500.json
python -m mycelium.cli baseline --url http://localhost:8081 --model $M --suite simpleqa --limit 100 --workers 4 --out reports/gpu/$M-simpleqa.json
python -m mycelium.cli baseline --url http://localhost:8081 --model $M --suite humanevalplus --limit 50 --workers 4 --out reports/gpu/$M-humanevalplus.json
python -m mycelium.cli baseline --url http://localhost:8081 --model $M --suite mbppplus --limit 50 --workers 4 --out reports/gpu/$M-mbppplus.json
# stop the server (Ctrl+C), then LFM3-1.7B (no MTP head; --jinja for its chat template):
llama-server -m models/LFM3-1.7B-Q8_0.gguf -ngl 99 -c 16384 -np 4 --reasoning off --jinja --port 8081
# repeat the six baseline lines with M=lfm3-1.7b, then:
python -m mycelium.cli compare reports/gpu/*.json
```

Before each model's six runs, send one request with `curl` and check the reply ends with
`ANSWER:` and `CONFIDENCE:` lines. While a server runs, note VRAM from `nvidia-smi`.
The code suites (HumanEval+, MBPP+) run the model's code locally with a 30 s timeout per
problem; there is no sandbox yet (T007), so run them only on a machine you are fine with that on.

Hosted teacher (T005): put the key in an environment variable and pass its *name*:

```bash
export DEEPSEEK_API_KEY=...        # in your shell profile, not in the repo
python -m mycelium.cli e2e --teacher-url https://api.deepseek.com --teacher-model <id from DeepSeek docs> \
    --teacher-api-key-env DEEPSEEK_API_KEY
```

Kill test with the student (T015a): see `specs/003-insight-kill-test/quickstart.md`.

After each task: write the command, hardware and numbers into `research.md`, tick the task in `tasks.md`, keep `pytest -q` green.
