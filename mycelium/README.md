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
pytest -q                          # 109 tests, ~60 s
python -m mycelium.cli e2e --out report.json
python -m mycelium.cli e2e --index binary-ivf
python -m mycelium.cli bench --n 1000000   # compare HIKMAT indexes
python -m mycelium.cli insights --suite real   # does memory pay? sweep of hint assumptions (~4 min)
python -m mycelium.cli killtest --mock         # spec 003 harness check (~10 s)
python -m mycelium.cli doctor                  # what this machine can run
python -m mycelium.cli baseline --url http://localhost:8081 --model qwen3.5-2b --workers 4   # P0: one real model alone
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
  0   0.917     46.5  0.925 /  42.9        0.00      0.91      0.750   False
  1   0.967     36.8  0.950 /  40.9        0.27      0.68      0.750   False
  ...
  3   0.900     34.0  0.908 /  38.4        0.33      0.65      0.750   True   <- poison rolled back
```

Days 1–5, seed 0: cost 36.3 vs 42.7 for teacher-only, accuracy 0.908 vs 0.898. Seeds 1–3: cost 28.2–31.9 vs 41.8–43.2, accuracy 0.902–0.918 vs 0.895–0.907. These savings rest on an assumed hint effect; see "Do insights work?" below.

### On real questions (`--suite real`)

330 real questions committed under `mycelium/data/samples/` (MIT): 80 GSM8K word problems, and 250 MMLU questions across high-school and conceptual physics, high-school and elementary mathematics (incl. geometry), high-school and college biology, high-school chemistry, astronomy, medical genetics and high-school computer science. 40 fictional-entity questions are added so abstaining can be measured. Split: 50% train, 30% holdout, 20% golden.

`--scenario complex` adds topic drift (a rotating group of subjects is 4× more frequent each day), a student that is most overconfident where it is weakest (chemistry and physics), and a teacher with a blind spot in chemistry.

| Seed 0 | Basic | Complex |
|---|---|---|
| Student accuracy: baseline → distill → RLCR | 0.51 → 0.67 → 0.73 | 0.49 → 0.64 → 0.73 |
| Student ECE: baseline → RLCR | 0.25 → 0.10 | 0.29 → 0.05 |
| Router alone (tuned on holdout) | no cheaper than the teacher → `teacher_only` | same |
| Mean cost, days 1–5: HIKMAT / same router without memory / teacher-only | 22.0 / 26.3 / 24.6 | 29.1 / 32.4 / 30.5 |
| Accuracy, days 1–5: HIKMAT / without memory / teacher-only | 0.923 / 0.950 / 0.955 | 0.918 / 0.932 / 0.933 |
| Hinted answers whose insight came from the same question | 57% | 55% |
| Golden accuracy without → with memory | 0.80 → 0.81 | 0.80 → 0.81 |
| Quarantined poison / forced poison / tampering | rejected / rolled back / detected | same |

With the default assumption (`hint_gain` 0.4), memory makes the system 5–11% cheaper than asking the teacher every time (the router alone is 6–7% more expensive), and it costs 1.5–3.2 points of accuracy. The accuracy loss is the router answering more questions itself: its thresholds are tuned to reach 90% of the teacher's accuracy, and memory moves it toward that floor. The test split holds only 3–7 questions per subject, so per-subject numbers are noisy. The students and teacher are simulated; only the questions are real.

An earlier version reported 36–42% savings here. That number assumed an insight from one MMLU question helps on a different question of the same subject. It doesn't (one astronomy fact doesn't answer another astronomy question), and with that removed most of the saving went away.

### Do insights work?

Short answer: the machinery works, the benefit is unproven. The mock student is *told* how much a hint helps (`hint_gain`) and how much of that carries to a different problem of the same family (`procedural_transfer`), so a single run can't show that insights help. `python -m mycelium.cli insights --suite real` sweeps both and compares against the same router without memory (seed 0, days 1–5):

| `hint_gain` | Synthetic: Δcost / Δaccuracy | Real basic: Δcost / Δaccuracy | Real complex: Δcost / Δaccuracy | Promoted (real basic) |
|---|---|---|---|---|
| −0.2 (hints hurt) | −0.1 / 0 | −0.1 / 0 | −0.1 / 0 | 0 |
| 0 (hints do nothing) | −0.1 / 0 | −0.1 / 0 | −0.1 / 0 | 2 * |
| 0.1 | +0.8 / 0 | +0.9 / 0 | +0.7 / 0 | 110 |
| 0.2 | +3.1 / +0.005 | +2.4 / −0.013 | +1.2 / 0 | 144 |
| 0.4 (default) | +9.9 / +0.013 | +4.4 / −0.027 | +3.3 / −0.013 | 162 |

Δcost is the saving per question vs the same router without memory (positive = cheaper); Δaccuracy is HIKMAT minus no-memory. `procedural_transfer` (0, 0.25, 0.5) changed real-suite savings by at most 0.5 and synthetic ones not at all. \* On the poison day, a correct insight that displaces a forced-in bad one helps, so it is promoted.

What this shows: useless and harmful insights are rejected (that is what the autopilot is for), and memory pays only as much as hints really help: at `hint_gain` 0.1 the saving is under 1 per question (about 4%). Whether it does is the first thing spec 002 measures (task T015a: GSM-Symbolic templates, 50 variants each).

**When problems really share a method (`--suite symbolic`).** GSM8K questions are all different, so a remembered method rarely fits another question. Apple's GSM-Symbolic (committed, 5,000 rows) turns 100 GSM8K questions into templates with 50 variants each: new names and numbers, same reasoning. The symbolic suite uses 40 templates × 6 variants plus the MMLU questions. Same sweep, seed 0, days 1–5, against the same router without memory:

| `hint_gain` | `procedural_transfer` 0 | 0.25 | 0.5 |
|---|---|---|---|
| 0 | +0.1 / −0.002 | same | same |
| 0.1 | +2.0 / +0.002 | +2.8 / 0 | +2.6 / −0.005 |
| 0.4 | +8.4 / +0.017 | +7.8 / +0.015 | +8.0 / +0.032 |

(saving per question / Δaccuracy; no-memory router: cost 22.7, accuracy 0.89; teacher-only: 27.6, 0.943.) With repeating methods, memory improves cost and accuracy together, unlike on plain GSM8K. It is still the assumed `hint_gain` doing the work; T015a replaces it with a measurement.

**The kill test (spec 003).** `python -m mycelium.cli killtest --url http://localhost:8081 --model student` takes 50 GSM-Symbolic templates, uses variant 0's verified solution as the stored insight, and solves 10 new variants of each three ways: no hint, the insight from the same template, and the insight from a different template of the same size. It reports accuracy and tokens per condition, paired differences with 95% intervals (bootstrap over templates), the mock parameters that reproduce the result, and a verdict (`pays`, `kill`, `inconclusive`) decided by rules written in `specs/003-insight-kill-test/research.md` before any real run. On the mock (`--mock`, true `hint_gain` 0.4) it reports `pays` and a fitted `hint_gain` of 0.38 [0.32, 0.45]. It has not run on a real model yet: this container can't download model weights. Weaknesses that remain in this simulation are listed in `docs/decisions.md` → "Do insights work?".

### Recursive self-improvement (spec 006)

`python -m mycelium.cli rsi` runs a self-improvement loop on the weights, not just the memory. Each generation the model attempts fresh math and code problems, keeps the ones at its frontier, trains a copy on its own verified solutions (plus some teacher traces as an anchor), and the copy replaces it only if its exam gain (golden set + held-out problems it never trains on) has a 95% lower bound above zero and hallucination doesn't rise. It stops on a plateau, or when its own problems improve but the exam doesn't (Goodhart). A bandit picks the next recipe (difficulty band, breadth) by measured exam gain: the loop improves how it improves, but can't touch JUDGE, the golden set or the gates.

Mock, seed 0: exam accuracy 0.778 → 0.972 in 8 generations (4 promoted). With a verifier that keeps only wrong traces nothing is promoted; with no verifier at all, rounds with many wrong traces are rejected and the model never ends worse. The gains come from the mock's learning rule; whether self-training helps a real 2B model is the pre-registered kill test in `specs/006-rsi/research.md`.

## What we learned building it

- **Calibration is not discrimination.** After RLCR the mock student is calibrated, but at ~72% accuracy many answers sit near 0.7 confidence, where right and wrong look alike. Matching the teacher's honesty without memory saves almost nothing. HIKMAT closes that gap by lifting confidence on problem types the system has already verified.
- **The router must tell the model how sure it needs to be.** If the model stops thinking at 0.85 while the router needs 0.9, the system pays for an expensive fallback every time. `answer(..., stop_at=...)` fixes that.
- **Look up memory before reasoning, not after.** A lookup costs about a tenth of a loop.
- **IDs must never repeat after a rollback**, or audit logs point at the wrong record.
- **Memory has to stay fast as it grows.** The first version rebuilt its search matrix on every lookup and recounted bytes on every insert: 36 ms per lookup and quadratic inserts at 50k insights. A real vector index fixed it (numbers below).
- **Cache the teacher.** Router tuning replays the same problems through ~100 settings. The cache cut teacher calls from 8,433 to 1,346 in the default run (the no-memory comparison added more replays).

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

## Next steps

Every next task, in order, is in [`specs/ROADMAP.md`](specs/ROADMAP.md), with markers for what needs the GPU PC (`[GPU]`) and what needs the owner's decision (`[OWNER]`). On a fresh clone, run `python -m mycelium.cli doctor` to see which tasks this machine can run. In short:

1. Small model first: the untrained student `Qwen3.5-2B-Q8_0.gguf` (2 GB) as the baseline (`python -m mycelium.cli baseline`) and the first kill-test reading.
2. Then the teacher on the 3090 (`Qwen3.8-27B-GSQ-RCO-IQ3_S.gguf`, 11.8 GB) and a real-teacher run.
3. Trustworthy evals: MATH-500, HumanEval+/MBPP+, SimpleQA, TruthfulQA, a code sandbox, a private holdout, a second JUDGE.
4. Real student (`Qwen/Qwen3.5-2B`): SFT, logit distillation, GRPO with the RLCR reward.
5. Decisive kill test with the trained student; hidden-state HIKMAT keys only if it says `pays`.
6. GSQ + RCO student builds, then phones (spec 004) and the insight hub (spec 005).

Intended license: AGPL-3.0-or-later (full license text to be added with the open-source launch).
