"""Backend for any OpenAI-compatible chat endpoint.

Works with llama.cpp's `llama-server`, vLLM, SGLang, Ollama and LM Studio, so a real
teacher (for example a GSQ-RCO GGUF of Qwen3.8-27B on a 3090) plugs into the same
pipeline as the mock. The model is asked to end with an ANSWER line and a CONFIDENCE
line, the verbalized confidence format RLCR trains for.

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

SYSTEM_PROMPT = (
    "Solve the task. End your reply with exactly these two lines:\n"
    "ANSWER: <final answer only>\n"
    "CONFIDENCE: <probability from 0 to 1 that your answer is correct>\n"
    "For coding tasks, put the complete function in a ```python code block before those lines "
    "and write `ANSWER: see code`.\n"
    "If the question cannot be answered from what you know, write `ANSWER: I don't know` "
    "and a low confidence."
)
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


def parse_reply(content: str, domain: str) -> ParsedReply:
    answers = _ANSWER.findall(content)
    answer = answers[-1] if answers else content.strip().splitlines()[-1] if content.strip() else ""
    confidences = _CONFIDENCE.findall(content)
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
        messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": problem.prompt}]
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
            content = reply["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as exc:
            raise BackendError(f"unexpected response shape from {self.base_url}: {reply!r:.200}") from exc
        tokens = reply.get("usage", {}).get("completion_tokens") or max(1, len(content) // 4)
        parsed = parse_reply(content, problem.domain)
        return Answer(
            text=parsed.text,
            confidence=parsed.confidence,
            loops=max(1, math.ceil(tokens / self.tokens_per_loop)),
            abstained=parsed.abstained,
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
