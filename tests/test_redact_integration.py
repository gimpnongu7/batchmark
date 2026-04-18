"""Integration tests: redact applied through result in report pipeline."""
import pytest
from batchmark.redact import RedactConfig, redact_result_dict, load_redact_config


def make_result_dict(command, stdout="", stderr="", status="success", duration=0.1):
    return {
        "command": command,
        "stdout": stdout,
        "stderr": stderr,
        "status": status,
        "duration": duration,
        "returncode": 0,
    }


@pytest.fixture
def redact_cfg():
    return RedactConfig(
        patterns=[r"password=\S+", r"token=[^\s]+"],
        placeholder="***",
        redact_env_keys=["SECRET"],
    )


def test_pipeline_command_redacted(redact_cfg):
    d = make_result_dict("curl -H token=abc123 http://x")
    out = redact_result_dict(d, redact_cfg)
    assert "abc123" not in out["command"]
    assert "***" in out["command"]


def test_pipeline_stdout_redacted(redact_cfg):
    d = make_result_dict("cmd", stdout="password=hunter2 ok")
    out = redact_result_dict(d, redact_cfg)
    assert "hunter2" not in out["stdout"]


def test_pipeline_non_sensitive_unchanged(redact_cfg):
    d = make_result_dict("echo hello", stdout="hello", stderr="")
    out = redact_result_dict(d, redact_cfg)
    assert out["command"] == "echo hello"
    assert out["stdout"] == "hello"


def test_pipeline_original_dict_not_mutated(redact_cfg):
    d = make_result_dict("run token=xyz")
    original_cmd = d["command"]
    redact_result_dict(d, redact_cfg)
    assert d["command"] == original_cmd


def test_load_and_apply_from_raw_config():
    raw = {
        "redact": {
            "patterns": [r"secret\S+"],
            "placeholder": "HIDDEN",
            "env_keys": [],
        }
    }
    cfg = load_redact_config(raw)
    d = make_result_dict("run secretABC")
    out = redact_result_dict(d, cfg)
    assert "HIDDEN" in out["command"]
    assert "secretABC" not in out["command"]
