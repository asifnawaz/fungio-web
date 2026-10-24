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
| ORACLE | Teacher model (planned: Qwen3.8-27B, 4-bit) | `models/mock.py` (`make_teacher`) |
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
pip install -e ".[dev]"
pytest -q                                   # 39 tests, ~15 s
python -m mycelium.cli e2e --out report.json
```

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

## Design rules the code enforces

- The model never grades itself. JUDGE is deterministic code.
- The golden set is fingerprinted (`GoldenSet`). Changing it raises `TamperError` instead of quietly making the exam easier.
- Insights enter quarantine. Facts (verify level 2) need two independent confirmations before review.
- The health baseline only moves up, so slow drift can't creep past the limits.
- Memory has a hard byte budget. The least valuable records are evicted first, and stale quarantine entries expire.
- Insights carry the model version and are ignored by a different version.

## Not done yet (next steps on a GPU machine)

- Real backends behind `ModelBackend` / `TrainableBackend`: ORACLE via llama.cpp or vLLM, SPROUT fine-tuning via TRL/Unsloth (SFT, logit distillation, GRPO with the RLCR reward).
- HIKMAT keys from real hidden states (middle-layer pooling) instead of synthetic features, and an ANN index (FAISS) instead of brute-force search.
- A real code sandbox. `judge_code` only isolates the process.
- Real eval suites (GSM8K, MATH-500, HumanEval/MBPP, factual QA with unanswerables) and a private holdout.

Intended license: AGPL-3.0-or-later (full license text to be added with the open-source launch).
