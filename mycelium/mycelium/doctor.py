"""`python -m mycelium.cli doctor`: what this machine can run, so an agent doesn't guess.

Checks the things the roadmap's task markers depend on: Python and packages ([CPU]),
an NVIDIA GPU with enough memory ([GPU]), llama.cpp and the Hugging Face CLI on PATH,
free disk space, and optionally whether Hugging Face is reachable. Prints a JSON report
and which kinds of tasks are runnable here.
"""

from __future__ import annotations

import importlib.util
import platform
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

# Teacher GGUF 11.8 GB + student weights ~4.5 GB + student GGUF ~2 GB + datasets, caches, checkpoints.
MIN_FREE_DISK_GB = 40
MIN_VRAM_GB = 20


def _gpus() -> list[dict]:
    if shutil.which("nvidia-smi") is None:
        return []
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=20, check=True,
        ).stdout
    except (subprocess.SubprocessError, OSError):
        return []
    gpus = []
    for line in out.strip().splitlines():
        name, memory_mb, driver = (part.strip() for part in line.split(","))
        gpus.append({"name": name, "memory_gb": round(float(memory_mb) / 1024, 1), "driver": driver})
    return gpus


def _reachable(url: str, timeout: float = 5.0) -> bool:
    try:
        urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=timeout)
        return True
    except Exception:  # any failure means "not usable from here"
        return False


def check(path: Path = Path("."), network: bool = False) -> dict:
    gpus = _gpus()
    free_gb = round(shutil.disk_usage(path).free / 1024**3, 1)
    report = {
        "python": platform.python_version(),
        "python_ok": sys.version_info >= (3, 10),
        "os": f"{platform.system()} {platform.release()}",
        "packages": {name: importlib.util.find_spec(name) is not None for name in ("numpy", "faiss", "pytest", "ruff", "torch", "transformers", "trl")},
        "gpus": gpus,
        "gpu_ok": any(g["memory_gb"] >= MIN_VRAM_GB for g in gpus),
        "tools": {name: shutil.which(name) is not None for name in ("llama-server", "hf", "git")},
        "free_disk_gb": free_gb,
        "disk_ok": free_gb >= MIN_FREE_DISK_GB,
    }
    if network:
        report["huggingface_reachable"] = _reachable("https://huggingface.co")
    report["can_run"] = {
        "CPU": report["python_ok"] and report["packages"]["numpy"] and report["packages"]["pytest"],
        "GPU": report["gpu_ok"] and report["disk_ok"] and report["tools"]["llama-server"],
    }
    return report


def advice(report: dict) -> list[str]:
    """Plain next steps for whatever is missing."""
    tips = []
    if not report["python_ok"]:
        tips.append("Install Python 3.10 or newer.")
    if not report["packages"]["pytest"] or not report["packages"]["ruff"]:
        tips.append('Run: pip install -e ".[dev,faiss]"')
    if not report["gpus"]:
        tips.append("No NVIDIA GPU found (nvidia-smi missing or failing): only [CPU] tasks can run here.")
    elif not report["gpu_ok"]:
        tips.append(f"GPU has less than {MIN_VRAM_GB} GB: the 11.8 GB teacher plus the student won't fit; ask the owner.")
    if report["gpus"] and not report["tools"]["llama-server"]:
        tips.append("llama-server not on PATH: install or build llama.cpp with CUDA (spec 002 T001).")
    if not report["tools"]["hf"]:
        tips.append('Hugging Face CLI not on PATH: pip install -U "huggingface_hub[cli]"')
    if not report["disk_ok"]:
        tips.append(f"Only {report['free_disk_gb']} GB free; [GPU] tasks need about {MIN_FREE_DISK_GB} GB.")
    if report.get("huggingface_reachable") is False:
        tips.append("huggingface.co is not reachable: model and dataset downloads will fail.")
    return tips or ["Everything the roadmap needs is present."]
