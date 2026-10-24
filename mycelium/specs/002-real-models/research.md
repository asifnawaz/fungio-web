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
- The cloud dev container blocks `api.deepseek.com`; run this on the PC.

## Measured on the CPU container (spec 001)
- HIKMAT lookups at 1M keys: numpy 9.4 ms, faiss-hnsw 0.13 ms (98.0% right family), binary-ivf 0.12 ms (99.3%).
- Teacher cache: 8,433 → 1,346 calls per full run (`python -m mycelium.cli e2e`, seed 0).
- The simulated teacher is right ~93% of the time per unique prompt. Identical prompts get identical answers (as at temperature 0), so a whole code family can be wrong together.

## Open questions
- Q1 Does real-student calibration after RLCR separate right from wrong (AUROC) well enough for routing to save cost? The mock suggests calibration alone isn't enough and memory is what pays.
- Q2 Which middle layer of the student gives the best HIKMAT keys (family recall vs cost)?
- Q3 Do GSQ + RCO budgets hold quality on a 1.5–2B student as they do on 27B?
- Q4 Real llama.cpp flags for MTP speculative decoding with the `-mtp` builds: check llama.cpp docs before use.
