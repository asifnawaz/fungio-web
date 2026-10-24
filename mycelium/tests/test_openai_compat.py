import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import numpy as np
import pytest

from mycelium.evals.judges import judge
from mycelium.models.openai_compat import BackendError, OpenAICompatBackend, parse_reply
from mycelium.types import Hint, Problem


@pytest.fixture
def server():
    """Local stand-in for llama-server / vLLM: replies with whatever the test queues."""
    state = {"replies": [], "requests": [], "status": 200}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            state["requests"].append({"path": self.path, "body": body, "auth": self.headers.get("Authorization")})
            content, tokens = state["replies"].pop(0)
            payload = json.dumps(
                {"choices": [{"message": {"content": content}}], "usage": {"completion_tokens": tokens}}
            ).encode()
            self.send_response(state["status"])
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    httpd = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    state["url"] = f"http://127.0.0.1:{httpd.server_port}"
    yield state
    httpd.shutdown()


def _problem(domain="math", answer="42"):
    return Problem("p", domain, "What is 6 * 7?", answer, 0.5, f"{domain}:x", np.ones(4) / 2)


def test_math_answer_confidence_and_cost(server):
    server["replies"].append(("6 times 7.\nANSWER: 42\nCONFIDENCE: 0.93", 300))
    backend = OpenAICompatBackend(server["url"], "qwen3.8-27b-gsq", cost_per_loop=16, api_key="k")
    answer = backend.answer(_problem(), max_loops=4)
    assert (answer.text, answer.confidence, answer.loops) == ("42", 0.93, 2)
    assert judge(_problem(), answer)
    request = server["requests"][0]
    assert request["path"] == "/v1/chat/completions"
    assert request["body"]["max_tokens"] == 4 * 256 and request["body"]["temperature"] == 0.0
    assert request["auth"] == "Bearer k"


def test_hint_and_sampling_reach_the_request(server):
    server["replies"].append(("ANSWER: 42\nCONFIDENCE: 90%", 10))
    backend = OpenAICompatBackend(server["url"], "m")
    answer = backend.answer(_problem(), max_loops=1, hint=Hint("method:math:x", 0.91, 3), sample=2)
    assert answer.confidence == 0.9
    body = server["requests"][0]["body"]
    assert "method:math:x" in body["messages"][-1]["content"]
    assert body["temperature"] == 0.7 and body["seed"] == 2


def test_code_block_is_extracted_and_judged(server):
    reply = "Here:\n```python\ndef add(a, b):\n    return a + b\n```\nANSWER: see code\nCONFIDENCE: 0.8"
    server["replies"].append((reply, 50))
    problem = _problem("code", "assert add(2, 3) == 5")
    answer = OpenAICompatBackend(server["url"], "m").answer(problem, max_loops=2)
    assert answer.text.startswith("def add") and judge(problem, answer)


def test_abstention_and_missing_confidence():
    abstain = parse_reply("No such place.\nANSWER: I don't know\nCONFIDENCE: 0.1", "qa")
    assert abstain.abstained and abstain.confidence == 0.1
    bare = parse_reply("ANSWER: Paris", "qa")
    assert bare.text == "Paris" and bare.confidence == 0.5


def test_http_errors_become_backend_errors(server):
    server["status"] = 500
    server["replies"].append(("boom", 1))
    with pytest.raises(BackendError, match="HTTP 500"):
        OpenAICompatBackend(server["url"], "m").answer(_problem(), max_loops=1)
    with pytest.raises(BackendError):
        OpenAICompatBackend("http://127.0.0.1:9", "m", timeout_s=2).answer(_problem(), max_loops=1)
