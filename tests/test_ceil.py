"""Tests for batchmark/ceil.py"""
import math
import pytest
from batchmark.runner import CommandResult
from batchmark.ceil import (
    CeilConfig,
    parse_ceil_config,
    ceil_duration,
    ceil_results,
    ceil_summary,
)


def make_result(cmd: str, duration: float, rc: int = 0) -> CommandResult:
    return CommandResult(
        command=cmd, returncode=rc, stdout="", stderr="", duration=duration
    )


# --- parse_ceil_config ---

def test_parse_ceil_config_defaults():
    cfg = parse_ceil_config({})
    assert cfg.resolution == 0.1
    assert cfg.min_value is None
    assert cfg.max_value is None


def test_parse_ceil_config_custom():
    cfg = parse_ceil_config({"ceil": {"resolution": 0.5, "min_value": 0.5, "max_value": 10.0}})
    assert cfg.resolution == 0.5
    assert cfg.min_value == 0.5
    assert cfg.max_value == 10.0


def test_parse_ceil_config_invalid_resolution():
    with pytest.raises(ValueError, match="positive"):
        parse_ceil_config({"ceil": {"resolution": 0}})


# --- ceil_duration ---

def test_ceil_duration_already_on_boundary():
    cfg = CeilConfig(resolution=0.1)
    assert ceil_duration(0.3, cfg) == pytest.approx(0.3)


def test_ceil_duration_rounds_up():
    cfg = CeilConfig(resolution=0.1)
    result = ceil_duration(0.31, cfg)
    assert result == pytest.approx(0.4)


def test_ceil_duration_zero():
    cfg = CeilConfig(resolution=0.1)
    assert ceil_duration(0.0, cfg) == pytest.approx(0.0)


def test_ceil_duration_respects_min():
    cfg = CeilConfig(resolution=0.1, min_value=1.0)
    # 0.05 ceils to 0.1, but min_value pushes it to 1.0
    assert ceil_duration(0.05, cfg) == pytest.approx(1.0)


def test_ceil_duration_respects_max():
    cfg = CeilConfig(resolution=1.0, max_value=5.0)
    assert ceil_duration(9.1, cfg) == pytest.approx(5.0)


def test_ceil_duration_large_resolution():
    cfg = CeilConfig(resolution=5.0)
    assert ceil_duration(3.0, cfg) == pytest.approx(5.0)
    assert ceil_duration(5.0, cfg) == pytest.approx(5.0)
    assert ceil_duration(5.1, cfg) == pytest.approx(10.0)


# --- ceil_results ---

sample_results = [
    make_result("echo a", 0.12),
    make_result("echo b", 0.55),
    make_result("echo c", 1.001),
]


def test_ceil_results_count():
    cfg = CeilConfig(resolution=0.1)
    out = ceil_results(sample_results, cfg)
    assert len(out) == 3


def test_ceil_results_durations_rounded_up():
    cfg = CeilConfig(resolution=0.1)
    out = ceil_results(sample_results, cfg)
    assert out[0].duration == pytest.approx(0.2)
    assert out[1].duration == pytest.approx(0.6)
    assert out[2].duration == pytest.approx(1.1)


def test_ceil_results_preserves_command():
    cfg = CeilConfig(resolution=0.1)
    out = ceil_results(sample_results, cfg)
    assert [r.command for r in out] == [r.command for r in sample_results]


def test_ceil_results_does_not_mutate_originals():
    cfg = CeilConfig(resolution=0.1)
    original_durations = [r.duration for r in sample_results]
    ceil_results(sample_results, cfg)
    assert [r.duration for r in sample_results] == original_durations


# --- ceil_summary ---

def test_ceil_summary_keys():
    cfg = CeilConfig(resolution=0.1)
    ceiled = ceil_results(sample_results, cfg)
    s = ceil_summary(sample_results, ceiled)
    assert set(s.keys()) == {"count", "total_original", "total_ceiled", "added"}


def test_ceil_summary_added_is_non_negative():
    cfg = CeilConfig(resolution=0.1)
    ceiled = ceil_results(sample_results, cfg)
    s = ceil_summary(sample_results, ceiled)
    assert s["added"] >= 0
