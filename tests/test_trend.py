"""Tests for batchmark.trend."""
import pytest
from batchmark.runner import CommandResult
from batchmark.trend import (
    TrendConfig,
    TrendEntry,
    detect_trends,
    parse_trend_config,
    _slope,
    _mean,
)


def make_result(cmd: str, duration: float, status: str = "success") -> CommandResult:
    return CommandResult(command=cmd, duration=duration, returncode=0, stdout="", stderr="", status=status)


@pytest.fixture
def three_runs():
    return [
        [make_result("echo hi", 0.1), make_result("sleep 1", 1.0)],
        [make_result("echo hi", 0.15), make_result("sleep 1", 0.9)],
        [make_result("echo hi", 0.2), make_result("sleep 1", 0.8)],
    ]


def test_parse_trend_config_defaults():
    cfg = parse_trend_config({})
    assert cfg.window == 3
    assert cfg.stable_threshold == 0.05


def test_parse_trend_config_custom():
    cfg = parse_trend_config({"window": 5, "stable_threshold": 0.10})
    assert cfg.window == 5
    assert cfg.stable_threshold == 0.10


def test_detect_trends_returns_one_entry_per_command(three_runs):
    entries = detect_trends(three_runs)
    commands = [e.command for e in entries]
    assert "echo hi" in commands
    assert "sleep 1" in commands
    assert len(entries) == 2


def test_detect_trends_direction_up(three_runs):
    entries = detect_trends(three_runs, TrendConfig(window=1, stable_threshold=0.01))
    by_cmd = {e.command: e for e in entries}
    assert by_cmd["echo hi"].direction == "up"


def test_detect_trends_direction_down(three_runs):
    entries = detect_trends(three_runs, TrendConfig(window=1, stable_threshold=0.01))
    by_cmd = {e.command: e for e in entries}
    assert by_cmd["sleep 1"].direction == "down"


def test_detect_trends_stable():
    runs = [
        [make_result("ping", 0.5)],
        [make_result("ping", 0.5)],
        [make_result("ping", 0.5)],
    ]
    entries = detect_trends(runs, TrendConfig(window=1, stable_threshold=0.05))
    assert entries[0].direction == "stable"
    assert entries[0].pct_change == 0.0


def test_slope_positive():
    assert _slope([1.0, 2.0, 3.0]) > 0


def test_slope_negative():
    assert _slope([3.0, 2.0, 1.0]) < 0


def test_slope_flat():
    assert _slope([2.0, 2.0, 2.0]) == 0.0


def test_slope_single_value():
    assert _slope([5.0]) == 0.0


def test_pct_change_calculated(three_runs):
    entries = detect_trends(three_runs, TrendConfig(window=1))
    by_cmd = {e.command: e for e in entries}
    # first_mean=0.1, last_mean=0.2 → +100%
    assert abs(by_cmd["echo hi"].pct_change - 100.0) < 1.0


def test_single_run_returns_stable():
    runs = [[make_result("cmd", 1.0)]]
    entries = detect_trends(runs)
    assert entries[0].direction == "stable"
