# Contract: `HFStudent` (spec 002 T010–T013)

The real student is a class in `mycelium/models/hf_student.py` that implements the existing protocols in `mycelium/models/base.py` (`ModelBackend`, `TrainableBackend`). The pipeline must not change to use it.

## Model

- Default: `LiquidAI/LFM3-1.7B` (LFM Open License v1.0; facts in `specs/ROADMAP.md`, consequences in `docs/decisions.md`). Text-only causal LM. Its card loads it with `trust_remote_code=True`; prefer native `transformers` support if the installed version has `lfm3`, otherwise pin the revision. Write which one worked in `research.md`.
- Chat template: reasoning is on by default. Build prompts with `enable_thinking=False` so replies match the llama.cpp `--reasoning off` baseline (T001c); the card warns this can be inconsistent, so T010 checks that replies still end with `ANSWER:` / `CONFIDENCE:` lines.
- Tokenizer differs from the teacher's (128,000 vs 248,320 tokens): T012 needs a cross-tokenizer loss or stays sequence-level.

## Constructor

```python
HFStudent(
    model_id: str = "LiquidAI/LFM3-1.7B",
    *,
    device: str = "cuda",
    dtype: str = "bfloat16",
    tokens_per_loop: int = 256,     # one pipeline "loop" = this many generated tokens
    cost_per_loop: float = 1.0,     # the teacher stays at 16.0
    key_layer: int = 12,            # hidden state used as the HIKMAT key until T015 picks one
    adapter_dir: str | None = None, # LoRA adapter to load (output of learn_sft / learn_rlcr)
)
```

`name` = model id; `version` = model id plus an adapter suffix (`+sft1`, `+rlcr2`, …). Every training call changes `version`, so HIKMAT drops insights from the old model.

## `answer(problem, *, max_loops, hint=None, sample=0, stop_at=None) -> Answer`

- Messages: the same `SYSTEM_PROMPT` as `OpenAICompatBackend`, the problem prompt, and for a hint a second user message in exactly the same format (`A verified approach for a similar problem (similarity 0.xx): …`). Built with the tokenizer's chat template.
- Decoding: greedy for `sample == 0`; for `sample > 0`, temperature 0.7 with seed = `sample`. `max_new_tokens = max_loops * tokens_per_loop`.
- `stop_at` can't be enforced mid-generation; ignore it (as `OpenAICompatBackend` does) and say so in the docstring.
- Parse with `parse_reply` from `models/openai_compat.py`.
- Return `Answer(text, confidence, loops=ceil(tokens / tokens_per_loop), abstained, tokens=generated token count, latent=key)`, where `key` is the mean over the **prompt** tokens of `hidden_states[key_layer]` (index 0 is the embedding output), as float32, L2-normalized.

## `learn_sft(records: list[tuple[Problem, str]]) -> None`

- `records` are verified teacher replies (they already end with `ANSWER:` and `CONFIDENCE:` lines). Train a LoRA adapter with TRL's `SFTTrainer` on chat-formatted pairs; loss on the assistant turn only.
- Kernel library: Unsloth **or** Liger Kernel, chosen in T011 after checking which one supports `lfm3`; if neither does, plain TRL + PEFT with gradient checkpointing. Record the choice in `docs/decisions.md`.
- Stop the teacher server while training (24 GB). Save the adapter under `checkpoints/`, then reload it for inference.

## `learn_rlcr(samples: list[RLCRSample]) -> None`

- Use TRL's GRPO trainer, not a hand-written policy gradient (constitution VI). The prompts are the problems in `samples` (they already passed `rlcr.learnable_problems`). Reward per generated reply = `rlcr.rlcr_reward(judge(problem, parsed_answer), parsed_confidence)`.
- The given answers only select the problems; GRPO generates its own groups. Say this in the docstring.

## Tests (CPU, `tests/test_hf_student.py`)

- Skip the module when `torch` or `transformers` is missing (`pytest.importorskip`), so CI without them stays green.
- Build a tiny random model from a small LFM3 config (2 layers: one `conv`, one `full_attention`; hidden 64) and a toy tokenizer, with no download. If `lfm3` needs remote code, use any tiny causal LM config available offline and say so in the test. Check: `answer` returns an `Answer` with a normalized `latent` of the hidden size, `tokens` ≤ `max_loops * tokens_per_loop`, and a hint changes the prompt.
- One SFT step on 4 toy records lowers the training loss and changes `version`.
