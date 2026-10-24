# Quickstart: spec 002 on the GPU PC

```bash
git clone <repo> && cd <repo>/mycelium
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev,faiss]"
pytest -q                                          # must pass before anything else

python -m mycelium.cli doctor --network               # what this PC can run

# 1. Small-model baseline first (T001b): untrained student, 2 GB
hf download unsloth/Qwen3.5-2B-GGUF Qwen3.5-2B-Q8_0.gguf --local-dir models
llama-server -m models/Qwen3.5-2B-Q8_0.gguf -ngl 99 -c 8192 --port 8081
python -m mycelium.cli baseline --url http://localhost:8081 --model qwen3.5-2b --suite real --out reports/baseline-real.json
python -m mycelium.cli baseline --url http://localhost:8081 --model qwen3.5-2b --suite symbolic --out reports/baseline-symbolic.json
python -m mycelium.cli killtest --url http://localhost:8081 --model qwen3.5-2b \
    --trials reports/killtest-base.jsonl --out reports/killtest-base.json   # spec 003 T010a

# 2. Teacher (T002-T003)
hf download ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF Qwen3.8-27B-GSQ-RCO-IQ3_S.gguf --local-dir models
llama-server -m models/Qwen3.8-27B-GSQ-RCO-IQ3_S.gguf -ngl 99 -c 32768 --port 8080

# 3. Real-teacher run (T004)
python -m mycelium.cli e2e --teacher-url http://localhost:8080 --teacher-model qwen3.8-27b \
    --suite symbolic --out reports/real-teacher.json
```

Hosted teacher (T005): put the key in an environment variable and pass its *name*:

```bash
export DEEPSEEK_API_KEY=...        # in your shell profile, not in the repo
python -m mycelium.cli e2e --teacher-url https://api.deepseek.com --teacher-model <id from DeepSeek docs> \
    --teacher-api-key-env DEEPSEEK_API_KEY
```

Kill test with the student (T015a): see `specs/003-insight-kill-test/quickstart.md`.

After each task: write the command, hardware and numbers into `research.md`, tick the task in `tasks.md`, keep `pytest -q` green.
