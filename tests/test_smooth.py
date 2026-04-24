"""Tests for batchmark.smooth."""
from __future__ import annotations

import pytest
from batchmark.runner import CommandResult
from batchmark.smooth import (
    SmoothConfig,
    SmoothedResult,
    parse_smooth_config,
    smooth_results,
    _rolling_means,
)


def make_result(cmd: str, duration: float, status: str = "success") -> CommandResult:
    return CommandResult(command=cmd, duration=duration, status=status, stdout="", stderr="", returncode=0)


@pytest.fixture
def sample_results():
    return [
        make_result("echo a", 1.0),
        make_result("echo a", 3.0),
        make_result("echo a", 2.0),
        make_result("echo b", 4.0),
        make_result("echo b", 2.0),
    ]


def test_parse_smooth_config_defaults():
    cfg = parse_smooth_config({})
    assert cfg.window == 3
    assert cfg.per_command is True


def test_parse_smooth_config_custom():
    cfg = parse_smooth_config({"window": 5, "per_command": False})
    assert cfg.window == 5
    assert cfg.per_command is False


def test_rolling_means_single():
    assert _rolling_means([2.0], 3) == [2.0]


def test_rolling_means_window_larger_than_list():
    result = _rolling_means([1.0, 3.0], 5)
    assert result[0] == pytest.approx(1.0)
    assert result[1] == pytest.approx(2.0)


def test_rolling_means_exact_window():
    vals = [1.0, 2.0, 3.0]
    result = _rolling_means(vals, 3)
    assert result[2] == pytest.approx(2.0)


def test_smooth_results_returns_correct_count(sample_results):
    out = smooth_results(sample_results)
    assert len(out) == len(sample_results)


def test_smooth_results_per_command_isolates_groups(sample_results):
    cfg = SmoothConfig(window=2, per_command=True)
    out = smooth_results(sample_results, cfg)
    # first result for 'echo a': window=1, smoothed == raw
    assert out[0].smoothed_duration == pytest.approx(1.0)
    # second result for 'echo a': mean(1.0, 3.0) = 2.0
    assert out[1].smoothed_duration == pytest.approx(2.0)
    # first result for 'echo b': window=1, smoothed == raw
    assert out[3].smoothed_duration == pytest.approx(4.0)


def test_smooth_results_global_mode():
    results = [
        make_result("cmd", 1.0),
        make_result("cmd", 3.0),
        make_result("cmd", 5.0),
    ]
    cfg = SmoothConfig(window=2, per_command=False)
    out = smooth_results(results, cfg)
    assert out[0].smoothed_duration == pytest.approx(1.0)
    assert out[1].smoothed_duration == pytest.approx(2.0)
    assert out[2].smoothed_duration == pytest.approx(4.0)


def test_smooth_result_preserves_command_and_status(sample_results):
    out = smooth_results(sample_results)
    for sr, r in zip(out, sample_results):
        assert sr.command == r.command
        assert sr.status == r.status
        assert sr.raw_duration == r.duration


def test_smooth_result_window_size_stored(sample_results):
    cfg = SmoothConfig(window=4)
    out = smooth_results(sample_results, cfg)
    assert all(sr.window_size == 4 for sr in out)
