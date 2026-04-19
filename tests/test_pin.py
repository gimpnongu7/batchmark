import pytest
from batchmark.pin import PinConfig, parse_pin_config, pin_commands, pin_results
from batchmark.runner import CommandResult


def make_result(cmd, duration=1.0, status="success"):
    return CommandResult(command=cmd, returncode=0, stdout="", stderr="", duration=duration, status=status)


def test_parse_pin_config_defaults():
    cfg = parse_pin_config({})
    assert cfg.first == []
    assert cfg.last == []


def test_parse_pin_config_full():
    cfg = parse_pin_config({"pin": {"first": ["a"], "last": ["z"]}})
    assert cfg.first == ["a"]
    assert cfg.last == ["z"]


def test_pin_commands_first():
    cfg = PinConfig(first=["c"], last=[])
    result = pin_commands(["a", "b", "c"], cfg)
    assert result[0] == "c"
    assert set(result) == {"a", "b", "c"}


def test_pin_commands_last():
    cfg = PinConfig(first=[], last=["a"])
    result = pin_commands(["a", "b", "c"], cfg)
    assert result[-1] == "a"


def test_pin_commands_first_and_last():
    cfg = PinConfig(first=["b"], last=["a"])
    result = pin_commands(["a", "b", "c"], cfg)
    assert result[0] == "b"
    assert result[-1] == "a"
    assert result[1] == "c"


def test_pin_commands_missing_pinned_ignored():
    cfg = PinConfig(first=["x"], last=["y"])
    result = pin_commands(["a", "b"], cfg)
    assert result == ["a", "b"]


def test_pin_results_reorders():
    results = [make_result("a"), make_result("b"), make_result("c")]
    cfg = PinConfig(first=["c"], last=["a"])
    out = pin_results(results, cfg)
    assert out[0].command == "c"
    assert out[-1].command == "a"


def test_pin_results_preserves_all():
    results = [make_result("a"), make_result("b"), make_result("c")]
    cfg = PinConfig(first=["b"], last=[])
    out = pin_results(results, cfg)
    assert len(out) == 3
    assert {r.command for r in out} == {"a", "b", "c"}


def test_pin_results_no_config():
    results = [make_result("a"), make_result("b")]
    cfg = PinConfig()
    out = pin_results(results, cfg)
    assert [r.command for r in out] == ["a", "b"]
