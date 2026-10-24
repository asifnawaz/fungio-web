# MYCELIUM v0.1

A pipeline for a small model that is **honest about what it doesn't know**, **gets cheaper
the more it is used**, and **improves itself without a human babysitting it**.

This first version runs end to end on a **mock backend** (no GPU, no model weights), so
every stage, gate and safety check can be tested on a laptop. Real model backends plug
into the same interfaces next.

> The mock numbers below say nothing about real models. They show the plumbing works:
> each stage moves its metric the right way, and every safety gate fires when attacked.

## Codebook

| Name | What it is | Code |
|---|---|---|
| ORACLE | Teacher model (planned: Qwen3.8-27B, GSQ-RCO GGUF) | `models/mock.py` (`make_teacher`), `models/openai_compat.py` (real server) |
| SPROUT | Student model (planned: ~1.5–2B Qwen) | `models/mock.py` (`make_student`) |
| JUDGE | Deterministic verifiers: math match, code execution, QA match | `evals/judges.py` |
| RLCR | RL with calibration rewards (correctness − Brier) | `rlcr.py` |
| TRIAGE | Confidence router: memory lookup → answer / think / escalate / abstain | `router.py` |
| HIKMAT | Memory of verified insights, looked up by meaning | `hikmat/` |
| CODON | 2-bit latent codes (64 floats → 16 bytes) | `hikmat/codec.py` |
| AUTOPILOT | Quarantine → shadow test → promote/reject, health check → rollback | `autopilot.py` |

## Run it

```bash
cd mycelium
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"            # add ",faiss" for the FAISS indexes
pytest -q                          # 58 tests, ~35 s
python -m mycelium.cli e2e --out report.json
python -m mycelium.cli e2e --index binary-ivf
python -m mycelium.cli bench --n 1000000   # compare HIKMAT indexes
```

### With a real teacher

Any OpenAI-compatible server works: llama.cpp's `llama-server`, vLLM, SGLang, Ollama or LM Studio. On a 3090, the planned teacher is ISTA-DASLab's `Qwen3.8-27B-GSQ-RCO-IQ3_S.gguf` (11.8 GB, task-lossless per its card, runs unmodified in llama.cpp):

```bash
hf download ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF Qwen3.8-27B-GSQ-RCO-IQ3_S.gguf --local-dir models
llama-server -m models/Qwen3.8-27B-GSQ-RCO-IQ3_S.gguf -ngl 99 -c 32768 --port 8080
python -m mycelium.cli e2e --teacher-url http://localhost:8080 --teacher-model qwen3.8-27b
```

A hosted API works the same way; keep the key in an environment variable:

```bash
export DEEPSEEK_API_KEY=...   # never commit it or pass it on the command line
python -m mycelium.cli e2e --teacher-url https://api.deepseek.com --teacher-model <model id from DeepSeek's docs> \
  --teacher-api-key-env DEEPSEEK_API_KEY
```

No GPU or key? Run the simulated teacher, which answers over the same HTTP API:

```bash
python -m mycelium.cli sim-teacher --port 8080 &
python -m mycelium.cli e2e --teacher-url http://localhost:8080 --teacher-model sim-qwen
```

The teacher must end each reply with `ANSWER:` and `CONFIDENCE:` lines (the system prompt asks for this). Its answers are cached, so router tuning replays them instead of asking again.

**AI agents:** start with [`AGENTS.md`](AGENTS.md). Specs, plans and the task list live in [`specs/`](specs/).

## What the end-to-end run does

1. **P0 baseline:** evaluate teacher and student on a held-out suite (math, code, QA with unanswerable questions).
2. **P1 distill:** the teacher answers the training suite, JUDGE keeps only verified answers, the student learns from them.
3. **P2 RLCR:** GRPO-style updates with reward `1[correct] − (confidence − 1[correct])²`. Problems the student always or never solves are filtered out, and zero-variance groups are dropped.
4. **P3 TRIAGE:** tune the router's thresholds for the cheapest policy that reaches 90% of the teacher's accuracy **without hallucinating more than the teacher + 3 points**. If routing can't beat the teacher alone at that honesty, the report says `teacher_only`.
5. **P4 HIKMAT days:** solve a stream of recurring problem types. Escalations and long reasoning that pass JUDGE become insights. The autopilot shadow-tests them before use. On the poison day, a bad insight is sent through quarantine and two more are forced live, as if a verifier bug let them through.

Sample output (seed 0):

```
stage            student acc   ECE    halluc
P0 baseline      0.567       0.176  0.300
P1 distill       0.689       0.204  0.278
P2 RLCR          0.722       0.097  0.211
teacher          0.889       0.034  0.056

P4 HIKMAT (golden accuracy without memory: 0.689)
day   accuracy  cost   teacher-only acc/cost   retrieve  escalate  golden  rollback
  0   0.917     46.5  0.925 /  42.9        0.00      0.91      0.811   False
  1   0.975     34.3  0.950 /  40.9        0.33      0.61      0.811   False
  ...
  3   0.908     32.4  0.908 /  38.4        0.36      0.62      0.811   True   <- poison rolled back
```

Seeds 1–3 show the same pattern: from day 1 on, cost runs 35–45% below teacher-only at similar accuracy.

## What we learned building it

- **Calibration is not discrimination.** After RLCR the mock student is calibrated, but at ~72% accuracy many answers sit near 0.7 confidence, where right and wrong look alike. Matching the teacher's honesty without memory saves almost nothing. HIKMAT closes that gap by lifting confidence on problem types the system has already verified.
- **The router must tell the model how sure it needs to be.** If the model stops thinking at 0.85 while the router needs 0.9, the system pays for an expensive fallback every time. `answer(..., stop_at=...)` fixes that.
- **Look up memory before reasoning, not after.** A lookup costs about a tenth of a loop.
- **IDs must never repeat after a rollback**, or audit logs point at the wrong record.
- **Memory has to stay fast as it grows.** The first version rebuilt its search matrix on every lookup and recounted bytes on every insert: 36 ms per lookup and quadratic inserts at 50k insights. A real vector index fixed it (numbers below).
- **Cache the teacher.** Router tuning replays the same problems through ~100 settings. The cache cut teacher calls from 7,688 to 1,346 in the default run.

## Optimization stack

Libraries chosen per stage, so nothing here reinvents what already exists:

| Stage | Library | Why |
|---|---|---|
| Teacher serving | llama.cpp `llama-server` (GGUF) on one GPU; vLLM or SGLang when batching many requests | Plugs in through `OpenAICompatBackend`. SGLang is strong on structured output and prefix caching. |
| Teacher weights | ISTA-DASLab GSQ-RCO GGUF builds (e.g. Qwen3.8-27B) | 1–3 bit weights leave VRAM on a 24 GB card for long context and the student |
| Giant MoE models | Strata / Maya (GPU + RAM + SSD tiers) | Later: testbed for task-aware expert prefetch |
| Student fine-tuning (SFT, GRPO with the RLCR reward) | TRL with **either** Unsloth **or** Liger Kernel | Fused kernels cut VRAM; using both double-patches the same layers |
| Student quantization | GSQ (post-training 1–3 bit) + RCO (per-tensor bits under an exact size budget) | Replaces the earlier ternary-training plan. RCO fits one model to each device budget (phone, laptop, PC). |
| HIKMAT search | NumPy (exact, default); FAISS binary IVF (XOR + popcount) for large memories | Measured below |
| Faster decoding (later) | Speculative decoding (EAGLE-3 / P-EAGLE style drafts, MTP heads) in the serving engine | 2–4x on typical workloads per published reports |

HIKMAT lookup speed on this machine (4 CPU cores, 64-dim clustered keys; `python -m mycelium.cli bench` reproduces it):

| Records | Before (rebuild per lookup) | `numpy` (exact) | `faiss-hnsw` (float graph) | `binary-ivf` (XOR + IVF) |
|---|---|---|---|---|
| 10,000 | 6.1 ms | 0.07 ms | 0.11 ms | same as numpy (exact below 10k) |
| 100,000 | (35.6 ms at 50k) | 0.58 ms | 0.07 ms, 99.6% right family | 0.08 ms, 100% right family |
| 1,000,000 | — | 9.4 ms | 0.13 ms, 98.0% right family, 131 s build | 0.12 ms, 99.3% right family, 41 s build |

Per key, `faiss-hnsw` keeps 256 bytes of floats plus its graph; `binary-ivf` searches 8 bytes of sign bits.

`binary-ivf` searches exactly until 10k records, then keeps each key's sign bits (64 dims → 8 bytes) in a FAISS binary IVF: only 8 clusters are scanned, Hamming distance (popcount of XOR) builds a shortlist, and the shortlist is reranked exactly. A plain XOR scan in NumPy was slower than the float product (2.8 ms vs 0.58 ms at 100k), so it isn't offered. Inserts went from quadratic (280 s for 50k) to ~0.4 ms each at 100k.

Which index to use: `numpy` up to ~100k records; `binary-ivf` beyond that. Its 8-byte keys also suit phones once reranking reads the 16-byte CODON codes instead of floats.

## Design rules the code enforces

- The model never grades itself. JUDGE is deterministic code.
- The golden set is fingerprinted (`GoldenSet`). Changing it raises `TamperError` instead of quietly making the exam easier.
- Insights enter quarantine. Facts (verify level 2) need two independent confirmations before review.
- The health baseline only moves up, so slow drift can't creep past the limits.
- Memory has a hard byte budget. The least valuable records are evicted first, and stale quarantine entries expire.
- Insights carry the model version and are ignored by a different version.

## Not done yet (next steps on a GPU machine)

- A real student behind `TrainableBackend`: SFT, logit distillation and GRPO with the RLCR reward via TRL + Unsloth (or Liger), then GSQ + RCO quantization. The teacher side already works through `OpenAICompatBackend`.
- HIKMAT keys from real hidden states (middle-layer pooling) instead of synthetic features.
- A real code sandbox. `judge_code` only isolates the process.
- Real eval suites (GSM8K, MATH-500, HumanEval/MBPP, factual QA with unanswerables) and a private holdout.

Intended license: AGPL-3.0-or-later (full license text to be added with the open-source launch).
