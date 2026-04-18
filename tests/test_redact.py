"""Tests for batchmark.redact."""
import pytest
from batchmark.redact import (
    RedactConfig,
    redact_string,
    redact_env,
    redact_result_dict,
    load_redact_config,
)


@pytest.fixture
def cfg():
    return RedactConfig(
        patterns=[r"secret\S*", r"token=[^\s]+"],
        placeholder="***",
        redact_env_keys=["AWS_SECRET", "API_KEY"],
    )


def test_redact_string_single_match(cfg):
    result = redact_string("run secretABC now", cfg)
    assert result == "run *** now"


def test_redact_string_multiple_patterns(cfg):
    result = redact_string("token=abc123 secret999", cfg)
    assert "***" in result
    assert "abc123" not in result
    assert "secret999" not in result


def test_redact_string_no_match(cfg):
    result = redact_string("echo hello", cfg)
    assert result == "echo hello"


def test_redact_env_replaces_sensitive(cfg):
    env = {"PATH": "/usr/bin", "AWS_SECRET": "supersecret", "API_KEY": "key123"}
    out = redact_env(env, cfg)
    assert out["PATH"] == "/usr/bin"
    assert out["AWS_SECRET"] == "***"
    assert out["API_KEY"] == "***"


def test_redact_env_case_insensitive(cfg):
    env = {"aws_secret": "val"}
    out = redact_env(env, cfg)
    assert out["aws_secret"] == "***"


def test_redact_env_no_mutation(cfg):
    env = {"FOO": "bar"}
    out = redact_env(env, cfg)
    assert out is not env


def test_redact_result_dict_command(cfg):
    d = {"command": "run secretXYZ", "stdout": "", "stderr": ""}
    out = redact_result_dict(d, cfg)
    assert "secretXYZ" not in out["command"]


def test_redact_result_dict_stdout_stderr(cfg):
    d = {"command": "echo", "stdout": "token=abc", "stderr": "secret123"}
    out = redact_result_dict(d, cfg)
    assert "abc" not in out["stdout"]
    assert "secret123" not in out["stderr"]


def test_load_redact_config_defaults():
    cfg = load_redact_config({})
    assert cfg.patterns == []
    assert cfg.placeholder == "***"
    assert cfg.redact_env_keys == []


def test_load_redact_config_full():
    raw = {"redact": {"patterns": ["pw\\S+"], "placeholder": "REDACTED", "env_keys": ["SECRET"]}}
    cfg = load_redact_config(raw)
    assert cfg.patterns == ["pw\\S+"]
    assert cfg.placeholder == "REDACTED"
    assert cfg.redact_env_keys == ["SECRET"]
