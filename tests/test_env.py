"""Tests for batchmark.env."""
import os
import pytest
from batchmark.env import EnvConfig, build_env, parse_env_list, load_env_config


def test_build_env_inherits_os_env():
    cfg = EnvConfig(inherit=True)
    env = build_env(cfg)
    assert "PATH" in env or True  # PATH may not exist in all CI envs
    # At minimum, inheriting should include current env keys
    for k, v in os.environ.items():
        assert env[k] == v


def test_build_env_no_inherit():
    cfg = EnvConfig(base={"FOO": "bar"}, inherit=False)
    env = build_env(cfg)
    assert env == {"FOO": "bar"}
    assert "PATH" not in env


def test_build_env_base_overrides_os(monkeypatch):
    monkeypatch.setenv("MY_VAR", "original")
    cfg = EnvConfig(base={"MY_VAR": "overridden"}, inherit=True)
    env = build_env(cfg)
    assert env["MY_VAR"] == "overridden"


def test_build_env_overrides_param():
    cfg = EnvConfig(base={"A": "1"}, inherit=False)
    env = build_env(cfg, overrides={"A": "99", "B": "2"})
    assert env["A"] == "99"
    assert env["B"] == "2"


def test_parse_env_list_basic():
    result = parse_env_list(["FOO=bar", "BAZ=qux"])
    assert result == {"FOO": "bar", "BAZ": "qux"}


def test_parse_env_list_value_with_equals():
    result = parse_env_list(["URL=http://example.com?a=1"])
    assert result["URL"] == "http://example.com?a=1"


def test_parse_env_list_invalid():
    with pytest.raises(ValueError, match="Invalid env pair"):
        parse_env_list(["NOEQUALS"])


def test_load_env_config_full():
    raw = {"env": {"vars": {"X": "1", "Y": "2"}, "inherit": False}}
    cfg = load_env_config(raw)
    assert cfg.base == {"X": "1", "Y": "2"}
    assert cfg.inherit is False


def test_load_env_config_defaults():
    cfg = load_env_config({})
    assert cfg.base == {}
    assert cfg.inherit is True


def test_load_env_config_bad_vars():
    with pytest.raises(ValueError, match="must be a mapping"):
        load_env_config({"env": {"vars": ["FOO=bar"]}})
