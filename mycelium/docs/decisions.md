# Decisions, rejected options and the research track

The "why" behind MYCELIUM, distilled from the design discussions with the owner (Oct 2026). Newest decisions go at the top of each section.

## Product decisions
- **Free forever, open source.** No paid tier. Optional donations (never gating features). Intended license AGPL-3.0-or-later so derivatives stay open; "Fungio" name kept as a trademark.
- **On-device first.** Models and personal memory live on the user's device. A future insight hub shares only verified, anonymized insights (consensus across devices, server-side re-verification, signed packs, device reputation, differential privacy, opt-in).
- **No babysitting.** Users never review the model's learning. Implicit signals (rephrased questions, copied answers, code that later runs) plus automatic judges replace manual feedback; every change goes through the autopilot gates.
- **Free infrastructure.** Hugging Face for weights and packs, GitHub for code and CI, static site hosting for the web, volunteer GPUs for verification. No paid servers.

## Technical decisions
- **Teacher = Qwen3.8-27B GSQ-RCO `IQ3_S` GGUF (11.8 GB) on llama.cpp.** Task-lossless per its card and leaves VRAM on a 3090 for the student. DeepSeek-V4.1-Flash GSQ-RCO (231–266 GB with Engram tables) is too slow for bulk distillation on 24 GB + 32 GB RAM; kept as a Strata testbed.
- **Student compression = GSQ + RCO**, replacing the earlier plan of native ternary (BitNet-style) training: post-training, cheaper, and RCO fits one model to several exact size budgets.
- **Training = TRL + Unsloth or Liger, never both** (they patch the same kernels).
- **Distill from a trained model instead of pretraining from scratch.** Scratch pretraining of 1.5B on one 3090 would take months; renting 8×H100 would cost a few thousand dollars.
- **Lookup before reasoning; router passes `stop_at`; teacher answers cached.** Each was a measured fix (see README "What we learned").
- **HIKMAT index:** `numpy` (exact) by default; `binary-ivf` (XOR + popcount inside a FAISS binary IVF, exact rerank) beyond ~100k records. 1M keys: 0.12 ms vs 9.4 ms exact.
- **HIKMAT is not a semantic cache.** A semantic cache returns an old final answer for a similar question, which is wrong when the numbers differ. HIKMAT returns a verified *method* as a hint and the model solves the new problem. KV, prefix and prompt caches only help with token-identical prefixes and run inside the serving engine.
- **Facts vs hypotheses.** Memory entries carry source, date, verification level (1 machine-checked, 2 source-checked, 3 consistency-only, 4 unverifiable) and expiry. Only levels 1–2 count as facts; level-2 facts need two independent confirmations.

## Data decisions
- **Real questions for quality claims.** GSM8K and MMLU (both MIT) samples are committed; ARC was skipped because CC-BY-SA would add share-alike terms to the data files. Synthetic problems remain for plumbing tests only.
- **Samples came through the Hugging Face dataset viewer**, because this cloud container can't reach huggingface.co directly. The viewer flattens line breaks and escapes some Markdown characters; both are documented in `data/samples/ATTRIBUTION.md`. Two rows were spot-checked against the viewer independently.
- **Stand-in HIKMAT keys for real questions** mix the subject's direction (0.92) with a hashed bag-of-words of the question (0.39), so same-subject questions are similar (> 0.75) and different subjects aren't. Real runs must replace this with hidden states (spec 002, T015).

## Measured negative results (keep, don't repeat)
- **On real questions, memory cost ~2.5 accuracy points in the basic scenario** (0.930 vs 0.955 over days 1–5) while cutting cost ~36%. Not free; watch it with real models.
- **The article "A" was parsed as option A** ("A planet orbits…" → A). Caught by a test; option letters now need punctuation after a leading letter, and a lone "A" followed by a lowercase word is ignored.
- **Plain XOR scan in NumPy is slower than the float product** (2.8 ms vs 0.58 ms at 100k), because reranking needs the floats anyway. XOR only pays inside FAISS's IVF.
- **Calibration is not discrimination.** A calibrated ~72%-accurate student sits near 0.7 confidence on many answers, so matching the teacher's honesty without memory saved almost no cost. Memory is what lifts confidence where it is earned.
- **Self-consistency ("think") is the most expensive route** and was usually disabled by the tuner.
- **The first HIKMAT memory was O(n) per lookup and O(n²) to fill** (36 ms per lookup at 50k). Fixed by the index and a running byte count.

## Research track (unscheduled; each needs a cheap kill test first)
| Idea | One line | Precedent | Kill test |
|---|---|---|---|
| CODON latent language | compress middle-layer states of a teacher into a 2-bit code; humans only at the edges | VAE latents (Qwen-Image), Large Concept Models | train a bottleneck on one layer; measure output change |
| INNER-SPROUT | early layers as the small model; early/late agreement as free confidence | LayerSkip | AUROC of agreement vs correctness |
| FOLD | loop shared middle layers instead of unique ones | Relaxed Recursive Transformers, LoopFormer, LOTUS | fold a small model, heal by distillation |
| TRANSPLANT | keep a big model's first/last layers as ports, replace the middle with a small looped core | layer-dropping studies | drop or merge middle blocks; loss curve |
| CARTRIDGES | store DeltaNet state + compressed KV per document; load instead of re-reading | Stanford Cartridges | long-doc QA: cartridge vs re-read |
| DECISION-CODON / FRUIT | emit 64 four-way decisions per chunk in parallel | Clef heads, Infinity bitwise prediction | parallel vs sequential on cached codes |
| Engram over learned chunks | hash byte-chunk n-grams into lookup tables | DeepSeek Engram, H-Net | chunk-hash recall on a small LM |
| Task-aware expert prefetch | a decision model preloads a task's experts before decoding (exact output) | Strata/Maya tiers, MoE prefetch papers | offline cache simulation from expert logs |
| TRM-style deep supervision for language loops | train every loop step | Tiny Recursive Model | small looped LM with and without |
| H-Net bytes | drop the tokenizer for learned chunks | H-Net, BLT | 150M ablation vs BPE at equal FLOPs |
| Sleep consolidation | at idle, replay and distill frequently used insights into weights, then free memory | complementary learning systems | retention vs forgetting over simulated weeks |
| Cross-lingual HIKMAT | meaning-addressed memory lets Urdu queries reuse insights learned in English | shared multilingual concept features | same-problem recall across languages |

## Context on related work (Oct 2026, from searches)
- Decision models (Jev by TypeSafe; Cloudflare Clef/Clef-flash on Qwen backbones; Laya on ModernBERT) score typed options in one pass with calibrated probabilities. Clef reportedly trains with RLCD; the published method we use is RLCR (arXiv 2507.16806).
- Strata and Maya run very large MoE models across VRAM, RAM and SSD; Strata's README states predictors may reorder work but never change outputs.
- Low-bit families: BitNet b1.58 2B4T (ternary), GSQ (arXiv 2604.18556), RCO (arXiv 2605.00649).
