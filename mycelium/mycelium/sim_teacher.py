"""A simulated teacher behind a real OpenAI-compatible HTTP endpoint.

    python -m mycelium.cli sim-teacher --port 8080
    python -m mycelium.cli e2e --teacher-url http://localhost:8080 --teacher-model sim-qwen

It stands in for something like a Qwen3.8-27B GSQ-RCO GGUF served by llama-server, so
the whole pipeline can run through `OpenAICompatBackend` (HTTP, prompt format, reply
parsing, caching) without a GPU. It solves the synthetic suites from `evals.datasets`
by reading the prompt, looks up the committed GSM8K and MMLU samples by their exact
prompt, answers correctly with probability `accuracy` (per-family overrides model a
blind spot), picks a consistent distractor when wrong, writes some
reasoning text first, states a roughly calibrated confidence, sometimes formats that
confidence as a percentage or leaves it out, and abstains on entities it doesn't know.
Its quality numbers mean nothing about any real model.
"""

from __future__ import annotations

import functools
import json
import re
import threading
import time
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np

from mycelium.evals.datasets import CODE_TASKS, qa_world, stable_seed
from mycelium.evals.real import load_gsm_symbolic, load_real
from mycelium.types import MCQ_LETTERS

_MATH = [
    (re.compile(r"What is (-?\d+) \+ (-?\d+) \* (-?\d+)\?"), lambda a, b, c: a + b * c),
    (re.compile(r"What is (-?\d+) \+ (-?\d+)\?"), lambda a, b: a + b),
    (re.compile(r"What is (-?\d+) - (-?\d+)\?"), lambda a, b: a - b),
    (re.compile(r"What is (-?\d+) \* (-?\d+)\?"), lambda a, b: a * b),
    (re.compile(r"What is (-?\d+) mod (-?\d+)\?"), lambda a, b: a % b),
]
_CODE = re.compile(r"Write a Python function (\w+)\(")
_QA = re.compile(r"What is the (\w+) of (\w+)\?")


@dataclass
class SimConfig:
    accuracy: float = 0.93
    # Per-family accuracy overrides, e.g. {"mcq:high_school_chemistry": 0.6} for a blind spot.
    family_accuracy: dict[str, float] = field(default_factory=dict)
    hint_bonus: float = 0.04
    missing_confidence_rate: float = 0.05
    percent_confidence_rate: float = 0.2
    latency_s: float = 0.0
    seed: int = 0


@functools.lru_cache(maxsize=1)
def _real_answer_key() -> dict[str, tuple[str, str, str, str]]:
    """prompt -> (domain, family, right, wrong) for the committed GSM8K, MMLU and GSM-Symbolic samples."""
    key = {}
    for p in load_real() + load_gsm_symbolic():
        if p.domain == "mcq":
            wrong = [c for c in MCQ_LETTERS[: len(p.choices)] if c != p.answer]
            key[p.prompt] = ("mcq", p.family, p.answer, wrong[stable_seed("distractor", p.id) % len(wrong)])
        else:
            key[p.prompt] = ("math", p.family, p.answer, str(int(float(p.answer)) + 10))
    return key


def solve(prompt: str) -> tuple[str, str | None, str]:
    """Return (domain, correct answer text or None if unknown, wrong answer text)."""
    domain, _, right, wrong = _lookup(prompt)
    return domain, right, wrong


def _lookup(prompt: str) -> tuple[str, str | None, str | None, str]:
    """Return (domain, family or None, correct answer or None, wrong answer)."""
    real = _real_answer_key().get(prompt)
    if real:
        return real
    domain, right, wrong = _solve_synthetic(prompt)
    return domain, None, right, wrong


def _solve_synthetic(prompt: str) -> tuple[str, str | None, str]:
    for pattern, fn in _MATH:
        m = pattern.search(prompt)
        if m:
            value = fn(*map(int, m.groups()))
            return "math", str(value), str(value + 7)
    m = _CODE.search(prompt)
    if m and m.group(1) in CODE_TASKS:
        task = CODE_TASKS[m.group(1)]
        return "code", task.solution, task.buggy
    m = _QA.search(prompt)
    if m:
        answer = qa_world().get((m.group(1), m.group(2)))
        return "qa", answer, "Zorvexa"
    return "unknown", None, "42"


def reply(messages: list[dict], sample_seed: int, config: SimConfig) -> tuple[str, int]:
    prompt = next((m["content"] for m in messages if m["role"] == "user"), "")
    hinted = sum(1 for m in messages if m["role"] == "user") > 1
    domain, family, right, wrong = _lookup(prompt)
    rng = np.random.default_rng(stable_seed("sim-teacher", config.seed, prompt, sample_seed))
    reasoning = "Let me work through this step by step. " * int(rng.integers(3, 12))

    if right is None:
        lines = [reasoning, "I do not have reliable information about this.", "ANSWER: I don't know",
                 f"CONFIDENCE: {rng.uniform(0.05, 0.2):.2f}"]
        return "\n".join(lines), int(rng.integers(80, 200))

    base = config.family_accuracy.get(family, config.accuracy) if family else config.accuracy
    p = min(0.99, base + (config.hint_bonus if hinted else 0.0))
    correct = rng.random() < p
    answer = right if correct else wrong
    stated = float(np.clip((p if correct else 1 - p + 0.5) + rng.normal(0, 0.05), 0.05, 0.99))

    if domain == "code":
        body = [reasoning, f"```python\n{answer}\n```", "ANSWER: see code"]
    else:
        body = [reasoning, f"ANSWER: {answer}"]
    roll = rng.random()
    if roll >= config.missing_confidence_rate:
        if roll < config.missing_confidence_rate + config.percent_confidence_rate:
            body.append(f"CONFIDENCE: {round(stated * 100)}%")
        else:
            body.append(f"CONFIDENCE: {stated:.2f}")
    return "\n".join(body), int(rng.integers(150, 700))


def make_server(host: str = "127.0.0.1", port: int = 8080, config: SimConfig | None = None) -> ThreadingHTTPServer:
    config = config or SimConfig()

    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, payload: dict) -> None:
            data = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path.rstrip("/") == "/v1/models":
                self._send(200, {"object": "list", "data": [{"id": "sim-qwen", "object": "model"}]})
            else:
                self._send(404, {"error": "not found"})

        def do_POST(self):
            if self.path.rstrip("/") != "/v1/chat/completions":
                self._send(404, {"error": "not found"})
                return
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            if config.latency_s:
                time.sleep(config.latency_s)
            content, tokens = reply(body.get("messages", []), int(body.get("seed", 0)), config)
            tokens = min(tokens, int(body.get("max_tokens", tokens)))
            self._send(
                200,
                {
                    "object": "chat.completion",
                    "model": body.get("model", "sim-qwen"),
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
                    "usage": {"completion_tokens": tokens},
                },
            )

        def log_message(self, *args):
            pass

    return ThreadingHTTPServer((host, port), Handler)


def start_in_background(config: SimConfig | None = None) -> tuple[ThreadingHTTPServer, str]:
    """Start on a free local port; returns the server (call .shutdown()) and its base URL."""
    server = make_server(port=0, config=config)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_port}"
