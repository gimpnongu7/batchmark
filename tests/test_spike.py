"""Tests for batchmark.spike."""
import pytest
from batchmark.runner import CommandResult
from batchmark.spike import (
    SpikeConfig,
    SpikeEntry,
    detect_spikes,
    parse_spike_config,
)


def make_result(cmd: str, duration: float, status: str = "success") -> CommandResult:
    return CommandResult(command=cmd, duration=duration, status=status, stdout="", stderr="", returncode=0)


@pytest.fixture
def normal_results():
    return [make_result(f"cmd{i}", 1.0 + i * 0.01) for i in range(10)]


def test_parse_spike_config_defaults():
    cfg = parse_spike_config({})
    assert cfg.threshold == 2.0
    assert cfg.min_samples == 3
    assert cfg.window == 10


def test_parse_spike_config_custom():
    cfg = parse_spike_config({"threshold": 3.0, "min_samples": 5, "window": 7})
    assert cfg.threshold == 3.0
    assert cfg.min_samples == 5
    assert cfg.window == 7


def test_detect_spikes_returns_one_entry_per_result(normal_results):
    entries = detect_spikes(normal_results)
    assert len(entries) == len(normal_results)


def test_no_spike_before_min_samples():
    results = [make_result("cmd", 100.0) for _ in range(3)]
    cfg = SpikeConfig(threshold=2.0, min_samples=3)
    entries = detect_spikes(results, cfg)
    # first 3 items: at index 0,1 we have <3 prior, index 2 has exactly 2 prior
    assert all(not e.is_spike for e in entries[:2])


def test_spike_detected_above_threshold():
    base = [make_result("cmd", 1.0) for _ in range(5)]
    spike = make_result("cmd_spike", 10.0)
    results = base + [spike]
    cfg = SpikeConfig(threshold=2.0, min_samples=3, window=10)
    entries = detect_spikes(results, cfg)
    assert entries[-1].is_spike is True


def test_no_spike_within_threshold():
    base = [make_result("cmd", 1.0) for _ in range(5)]
    normal = make_result("cmd_ok", 1.5)
    results = base + [normal]
    cfg = SpikeConfig(threshold=2.0, min_samples=3, window=10)
    entries = detect_spikes(results, cfg)
    assert entries[-1].is_spike is False


def test_rolling_mean_is_none_before_min_samples():
    results = [make_result("cmd", 1.0) for _ in range(2)]
    cfg = SpikeConfig(threshold=2.0, min_samples=3, window=10)
    entries = detect_spikes(results, cfg)
    assert all(e.rolling_mean is None for e in entries)


def test_ratio_computed_correctly():
    base = [make_result("cmd", 2.0) for _ in range(5)]
    spike = make_result("cmd_spike", 8.0)
    results = base + [spike]
    cfg = SpikeConfig(threshold=2.0, min_samples=3, window=10)
    entries = detect_spikes(results, cfg)
    last = entries[-1]
    assert last.ratio is not None
    assert abs(last.ratio - 4.0) < 0.01


def test_window_limits_samples_used():
    # 20 slow results then a fast result; with window=5 mean should reflect last 5
    slow = [make_result("cmd", 10.0) for _ in range(20)]
    fast = make_result("cmd_fast", 0.1)
    results = slow + [fast]
    cfg = SpikeConfig(threshold=2.0, min_samples=3, window=5)
    entries = detect_spikes(results, cfg)
    last = entries[-1]
    assert last.rolling_mean is not None
    assert abs(last.rolling_mean - 10.0) < 0.01
