"""Backend for any OpenAI-compatible chat endpoint.

Works with llama.cpp's `llama-server`, vLLM, SGLang, Ollama and LM Studio, so a real
teacher (for example a GSQ-RCO GGUF of Qwen3.8-27B on a 3090) plugs into the same
pipeline as the mock. The model is asked to end with an ANSWER line and a CONFIDENCE
line, the verbalized confidence format RLCR trains for. The system prompt depends on the
domain, so code instructions never reach a math question.

Mapping to the pipeline's units: one "loop" is `tokens_per_loop` completion tokens, so
cost tracks how much the model actually generated. `stop_at` cannot be enforced through
a chat API and is ignored.
"""

from __future__ import annotations

import json
import math
import re
import urllib.error
import urllib.request
from dataclasses import dataclass

from mycelium.types import Answer, Hint, Problem

_FORMAT = (
    "Solve the task. End your reply with exactly these two lines:\n"
    "ANSWER: {answer}\n"
    "CONFIDENCE: <probability from 0 to 1 that your answer is correct>\n"
)
_ABSTAIN_RULE = "If the question cannot be answered from what you know, write `ANSWER: I don't know` and a low confidence."
# One prompt per domain. A single prompt that mentioned code for every task made a real 2B
# model (Qwen3.5-2B) answer math questions with `ANSWER: see code`.
SYSTEM_PROMPTS = {
    "math": _FORMAT.format(answer="<the final number only>") + _ABSTAIN_RULE,
    "code": _FORMAT.format(answer="see code")
    + "Put the complete function in a ```python code block before those two lines.\n" + _ABSTAIN_RULE,
    "mcq": _FORMAT.format(answer="<the letter of the correct option only>") + _ABSTAIN_RULE,
    "qa": _FORMAT.format(answer="<the answer only>") + _ABSTAIN_RULE,
}
SYSTEM_PROMPT = SYSTEM_PROMPTS["qa"]


def system_prompt(domain: str) -> str:
    return SYSTEM_PROMPTS.get(domain, SYSTEM_PROMPT)
DEFAULT_CONFIDENCE = 0.5
_ANSWER = re.compile(r"^\s*ANSWER:\s*(.*?)\s*$", re.IGNORECASE | re.MULTILINE)
_CONFIDENCE = re.compile(r"^\s*CONFIDENCE:\s*([0-9]*\.?[0-9]+)\s*(%?)", re.IGNORECASE | re.MULTILINE)
_CODE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)
_ABSTAIN = re.compile(r"^(i don'?t know|unknown|cannot be answered|not enough information)\.?$", re.IGNORECASE)


class BackendError(RuntimeError):
    pass


@dataclass(frozen=True)
class ParsedReply:
    text: str
    confidence: float
    abstained: bool


_BARE_PROBABILITY = re.compile(r"^\s*([0-9]*\.?[0-9]+)\s*(%?)\s*$")


def parse_reply(content: str, domain: str) -> ParsedReply:
    answers = _ANSWER.findall(content)
    confidences = _CONFIDENCE.findall(content)
    lines = [line for line in content.strip().splitlines() if line.strip()]
    # Only where an answer can't itself be a number in [0, 1] (unlike math).
    unlabelled = not answers and not confidences and len(lines) >= 2 and domain in ("mcq", "qa")
    bare = _BARE_PROBABILITY.match(lines[-1]) if unlabelled else None
    if bare and float(bare.group(1)) <= (100 if bare.group(2) else 1):
        # Small models sometimes drop both labels and end with "<answer>\n<probability>".
        answers, confidences = [lines[-2].strip()], [bare.groups()]
    answer = answers[-1] if answers else lines[-1] if lines else ""
    if confidences:
        value, percent = confidences[-1]
        confidence = float(value) / (100 if percent else 1)
    else:
        confidence = DEFAULT_CONFIDENCE
    confidence = min(max(confidence, 0.0), 1.0)
    if _ABSTAIN.match(answer.strip()):
        return ParsedReply("", confidence, abstained=True)
    if domain == "code":
        blocks = _CODE.findall(content)
        answer = blocks[-1].strip() if blocks else answer
    return ParsedReply(answer, confidence, abstained=False)


class OpenAICompatBackend:
    def __init__(
        self,
        base_url: str,
        model: str,
        *,
        name: str | None = None,
        version: str | None = None,
        cost_per_loop: float = 1.0,
        tokens_per_loop: int = 256,
        temperature: float = 0.0,
        sample_temperature: float = 0.7,
        timeout_s: float = 300.0,
        api_key: str | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.name = name or model
        self.version = version or model
        self.cost_per_loop = cost_per_loop
        self.tokens_per_loop = tokens_per_loop
        self.temperature = temperature
        self.sample_temperature = sample_temperature
        self.timeout_s = timeout_s
        self.api_key = api_key

    def answer(
        self,
        problem: Problem,
        *,
        max_loops: int,
        hint: Hint | None = None,
        sample: int = 0,
        stop_at: float | None = None,
    ) -> Answer:
        messages = [
            {"role": "system", "content": system_prompt(problem.domain)},
            {"role": "user", "content": problem.prompt},
        ]
        if hint is not None:
            messages.append(
                {"role": "user", "content": f"A verified approach for a similar problem (similarity {hint.similarity:.2f}): {hint.text}"}
            )
        body = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_loops * self.tokens_per_loop,
            # Attempt 0 is the deterministic answer; other attempts sample for self-consistency.
            "temperature": self.temperature if sample == 0 else self.sample_temperature,
            "seed": sample,
        }
        reply = self._post("/v1/chat/completions", body)
        try:
            message = reply["choices"][0]["message"]
            content = message.get("content") or ""
        except (KeyError, IndexError, TypeError, AttributeError) as exc:
            raise BackendError(f"unexpected response shape from {self.base_url}: {reply!r:.200}") from exc
        if not content.strip():
            # llama-server can route a thinking model's whole reply into `reasoning_content`
            # (seen with a Qwen3.5-2B GGUF unless the server runs with `--reasoning off`).
            content = message.get("reasoning_content") or ""
        tokens = reply.get("usage", {}).get("completion_tokens") or max(1, len(content) // 4)
        parsed = parse_reply(content, problem.domain)
        return Answer(
            text=parsed.text,
            confidence=parsed.confidence,
            loops=max(1, math.ceil(tokens / self.tokens_per_loop)),
            abstained=parsed.abstained,
            tokens=int(tokens),
        )

    def _post(self, path: str, body: dict) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(
            self.base_url + path, data=json.dumps(body).encode(), headers=headers, method="POST"
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:200]
            raise BackendError(f"{self.base_url} returned HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise BackendError(f"could not get a reply from {self.base_url}: {exc}") from exc
