"""The doctor must report what roadmap tasks can run here, without network by default."""

from mycelium import doctor


def test_report_has_what_the_roadmap_needs(tmp_path):
    report = doctor.check(tmp_path)
    assert {"python", "os", "packages", "gpus", "tools", "free_disk_gb", "can_run"} <= set(report)
    assert "huggingface_reachable" not in report  # no network unless asked
    assert report["can_run"]["CPU"]  # this test itself runs on a CPU with numpy and pytest
    assert isinstance(report["can_run"]["GPU"], bool)


def test_advice_names_what_is_missing():
    report = {
        "python_ok": True, "packages": {"pytest": True, "ruff": False}, "gpus": [], "gpu_ok": False,
        "tools": {"llama-server": False, "hf": False, "git": True}, "free_disk_gb": 10.0, "disk_ok": False,
    }
    tips = " ".join(doctor.advice(report))
    assert "pip install" in tips and "No NVIDIA GPU" in tips and "10.0 GB free" in tips
