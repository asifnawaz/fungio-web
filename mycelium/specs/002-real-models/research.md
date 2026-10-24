# Research 002: verified facts and open questions

Facts below were read from the model cards on Hugging Face (2026-10-24) unless marked otherwise.

## Teacher: ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF
| File | bpw | Size | Card note |
|---|---|---|---|
| `Qwen3.8-27B-GSQ-RCO-IQ2_XS.gguf` | 2.50 | 8.4 GB | zero-shot above BF16 |
| `Qwen3.8-27B-GSQ-RCO-IQ2_S.gguf` | 2.75 | 9.3 GB | matches base on AIME25 |
| `Qwen3.8-27B-GSQ-RCO-IQ3_XXS.gguf` | 3.00 | 10.1 GB | strong all-round |
| `Qwen3.8-27B-GSQ-RCO-IQ3_S.gguf` | 3.50 | 11.8 GB | recommended, task-lossless (AIME25 100.00, LCB v6 85.71, GPQA-D −0.51) |

- Standard GGUF; runs unmodified in llama.cpp, Ollama and LM Studio. License inherits Qwen3.8-27B (card: apache-2.0).
- Each file has an optional `-mtp` build (+~0.35 GB) carrying the Multi-Token Prediction head for speculative decoding in llama.cpp.
- **Choice:** `IQ3_S`. It leaves ~12 GB of VRAM on a 3090 for KV cache and the student. Fall back to `IQ3_XXS` if memory is tight.

## DeepSeek-V4.1-Flash-1017 GSQ-RCO (for later, not this spec)
- 763.2B parameters = 551.9B backbone + 196.6B in two **Engram** lookup tables. 384 routed experts per layer, 6 active per token, 1M context. MIT license.
- Builds: IQ1_M 1.75 bpw (231.32 GB total), IQ2_XXS 2.00 bpw (248.84 GB, 100.0% task recovery at reasoning effort 50), IQ2_XS 2.25 bpw (265.83 GB). The Engram file (110.60 GB) is shared and can stay memory-mapped on SSD.
- Card: "as of October 23, 2026, llama.cpp does not support DeepSeek-V4.1"; runs with Strata on a 12 GB GPU. The card links `github.com/Niko1221/Strata`; earlier notes used `github.com/ro99/strata`. Confirm the canonical repo before using either.
- On 24 GB VRAM + 32 GB RAM, most of the backbone streams from SSD. Expect low tokens/s (unmeasured). This is a good testbed for task-aware expert prefetch, not a practical bulk teacher.

## Hosted teacher (optional)
- DeepSeek's API is OpenAI-compatible. Use `--teacher-url https://api.deepseek.com --teacher-api-key-env DEEPSEEK_API_KEY` and take the model id from DeepSeek's docs (not verified here).
- Earlier the cloud container blocked `api.deepseek.com`; since 2026-10-24 it has full network access (the endpoint answers 401 without a key).

## Measured on the CPU container (spec 001)
- HIKMAT lookups at 1M keys: numpy 9.4 ms, faiss-hnsw 0.13 ms (98.0% right family), binary-ivf 0.12 ms (99.3%).
- Teacher cache: 8,433 → 1,346 calls per full run (`python -m mycelium.cli e2e`, seed 0).
- The simulated teacher is right ~93% of the time per unique prompt. Identical prompts get identical answers (as at temperature 0), so a whole code family can be wrong together.

## Baseline: untrained Qwen3.5-2B (T001b), first real model, 2026-10-24

Run in the cloud container, not the PC: 4-core Intel Xeon @ 2.10GHz (AVX-512, AMX), 15 GB RAM, no GPU. llama.cpp built from source at commit `8e5a58d` (2026-10-24) with `-DGGML_NATIVE=ON` (`-march=native`, AMX kernels compiled). Model `unsloth/Qwen3.5-2B-GGUF` `Qwen3.5-2B-Q8_0.gguf`, server `llama-server -c 16384 -np 4 -t 4 --reasoning off`.

`python -m mycelium.cli baseline --url http://127.0.0.1:8081 --model qwen3.5-2b --suite real` (111 holdout questions, sequential):

| Domain | n | Accuracy | ECE | Hallucination | Abstain |
|---|---|---|---|---|---|
| all | 111 | 0.577 | 0.359 | 0.423 | 0.045 |
| math (GSM8K) | 29 | 0.724 | 0.276 | 0.276 | 0.000 |
| mcq (MMLU science/math) | 70 | 0.543 | 0.288 | 0.457 | 0.000 |
| qa (fictional entities, unanswerable) | 12 | 0.417 | 0.979 | 0.583 | 0.417 |

989 s, 11.4 tokens/s end to end; 19.8% of replies had confidence exactly 0.5 (the parser's fallback, so likely a missing `CONFIDENCE:` line). Reading: the base student is strongly overconfident (ECE 0.36) and invents answers about entities that don't exist 58% of the time. That is the gap RLCR (calibration) training is meant to close.

**Problems found on the first real run (fixed, with tests):**
1. llama-server's default `--reasoning auto` put this GGUF's whole reply into `reasoning_content` and left `content` empty, although the model card says Qwen3.5-2B runs non-thinking by default. Run the server with `--reasoning off`; the client also falls back to `reasoning_content`.
2. One system prompt for all tasks mentioned code, and the model answered math with `ANSWER: see code`. Prompts are now per domain.
3. On MMLU the model sometimes ended with `A` and `0.99` on two lines, without labels. The parser accepts that for mcq/qa.

## Inference speed on CPU (same machine, 16 GSM8K questions, `bench_llm.py`-style run through `OpenAICompatBackend`)

| Config | Requests at once | Tokens/s (total) | Correct |
|---|---|---|---|
| Q8_0, plain | 1 | 19.6 | 7/16 |
| Q8_0, plain | 4 (`-np 4`) | 35.8 | 9/16 |
| Q8_0 MTP build, `--spec-type draft-mtp` | 1 | 22.3 | 8/16 |
| Q8_0 MTP build, `--spec-type draft-mtp` | 4 | **43.0** | 9/16 |
| Q4_K_M MTP build, `--spec-type draft-mtp` | 4 | 24.8 | 9/16 |

- Best here: the MTP build (`unsloth/Qwen3.5-2B-MTP-GGUF`, `Qwen3.5-2B-Q8_0.gguf`) with `--spec-type draft-mtp`, 4 server slots and `--workers 4` in our CLI: 2.2× the single-request speed. MTP draft acceptance was 0.74–0.81 (3.2–3.4 tokens per step), but on a CPU verifying drafts costs more, so MTP alone gave only +14%.
- Q4_K_M was *slower* than Q8_0 at 4 requests (24.8 vs 43.0): on this CPU, batched Q8_0 matmuls are faster than Q4_K dequantization. Measure again on the GPU; don't assume.
- Answers differ between 1 and 4 requests at once (7/16 vs 9/16 on the same questions at temperature 0): batched kernels change the arithmetic slightly. Compare conditions only under the same server settings (the kill test does).

## Open questions
- Q1 Does real-student calibration after RLCR separate right from wrong (AUROC) well enough for routing to save cost? The mock suggests calibration alone isn't enough and memory is what pays.
- Q2 Which middle layer of the student gives the best HIKMAT keys (family recall vs cost)?
- Q3 Do GSQ + RCO budgets hold quality on a 1.5–2B student as they do on 27B?
- Q4 (answered for CPU) MTP speculative decoding: `--spec-type draft-mtp` with an MTP GGUF build (llama.cpp `docs/speculative.md`). On the GPU, measure again for the teacher (`-mtp` builds of Qwen3.8-27B) and the student.
