import pytest
from batchmark.runner import CommandResult
from batchmark.burst import (
    BurstConfig,
    BurstEntry,
    parse_burst_config,
    detect_bursts,
    _count_in_window,
)


def make_result(cmd: str, duration: float = 0.1, status: str = "success") -> CommandResult:
    return CommandResult(command=cmd, duration=duration, status=status, stdout="", stderr="", returncode=0)


# --- parse_burst_config ---

def test_parse_burst_config_defaults():
    cfg = parse_burst_config({})
    assert cfg.window == 1.0
    assert cfg.max_in_window == 3
    assert cfg.cooldown == 0.5
    assert cfg.enabled is True


def test_parse_burst_config_custom():
    cfg = parse_burst_config({"burst": {"window": 2.0, "max_in_window": 5, "cooldown": 1.0, "enabled": False}})
    assert cfg.window == 2.0
    assert cfg.max_in_window == 5
    assert cfg.cooldown == 1.0
    assert cfg.enabled is False


def test_parse_burst_config_invalid_window():
    with pytest.raises(ValueError, match="window"):
        parse_burst_config({"burst": {"window": 0}})


def test_parse_burst_config_invalid_max():
    with pytest.raises(ValueError, match="max_in_window"):
        parse_burst_config({"burst": {"max_in_window": 0}})


def test_parse_burst_config_negative_cooldown():
    with pytest.raises(ValueError, match="cooldown"):
        parse_burst_config({"burst": {"cooldown": -1}})


# --- _count_in_window ---

def test_count_in_window_empty():
    assert _count_in_window([], 1.0, 1.0) == 0


def test_count_in_window_all_inside():
    assert _count_in_window([0.5, 0.6, 0.7], 1.0, 1.0) == 3


def test_count_in_window_some_outside():
    assert _count_in_window([0.0, 0.5, 0.9], 1.0, 0.5) == 2


# --- detect_bursts ---

def test_detect_bursts_returns_one_per_result():
    results = [make_result(f"cmd{i}") for i in range(4)]
    entries = detect_bursts(results)
    assert len(entries) == 4


def test_detect_bursts_no_throttle_below_limit():
    cfg = BurstConfig(window=10.0, max_in_window=5, cooldown=0.5)
    results = [make_result(f"cmd{i}") for i in range(3)]
    slept = []
    entries = detect_bursts(results, cfg, _sleep_fn=slept.append)
    assert all(not e.throttled for e in entries)
    assert slept == []


def test_detect_bursts_throttles_at_limit():
    cfg = BurstConfig(window=10.0, max_in_window=2, cooldown=0.25)
    results = [make_result(f"cmd{i}", duration=0.1) for i in range(4)]
    slept = []
    entries = detect_bursts(results, cfg, _sleep_fn=slept.append)
    throttled = [e for e in entries if e.throttled]
    assert len(throttled) >= 1


def test_detect_bursts_cooldown_applied_value():
    cfg = BurstConfig(window=10.0, max_in_window=1, cooldown=0.3)
    results = [make_result("a", duration=0.1), make_result("b", duration=0.1)]
    slept = []
    entries = detect_bursts(results, cfg, _sleep_fn=slept.append)
    throttled_entries = [e for e in entries if e.throttled]
    for e in throttled_entries:
        assert e.cooldown_applied == pytest.approx(0.3)


def test_detect_bursts_disabled_no_throttle():
    cfg = BurstConfig(window=10.0, max_in_window=1, cooldown=1.0, enabled=False)
    results = [make_result(f"cmd{i}") for i in range(5)]
    slept = []
    entries = detect_bursts(results, cfg, _sleep_fn=slept.append)
    assert all(not e.throttled for e in entries)
    assert slept == []


def test_detect_bursts_entry_fields():
    results = [make_result("echo hello", duration=0.2, status="success")]
    entries = detect_bursts(results)
    e = entries[0]
    assert e.command == "echo hello"
    assert e.duration == pytest.approx(0.2)
    assert e.status == "success"
