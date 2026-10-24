# Quickstart: spec 002 on the GPU PC

```bash
git clone <repo> && cd <repo>/mycelium
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev,faiss]"
pytest -q                                          # must pass before anything else

# Teacher (T002-T003)
hf download ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF Qwen3.8-27B-GSQ-RCO-IQ3_S.gguf --local-dir models
llama-server -m models/Qwen3.8-27B-GSQ-RCO-IQ3_S.gguf -ngl 99 -c 32768 --port 8080

# Real-teacher run (T004)
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
