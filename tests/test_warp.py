"""Tests for batchmark/warp.py"""
import pytest
from batchmark.runner import CommandResult
from batchmark.warp import (
    WarpConfig,
    WarpedResult,
    parse_warp_config,
    _warp_duration,
    warp_results,
    warp_summary,
)


def make_result(cmd="echo hi", duration=1.0, status="success", rc=0):
    return CommandResult(command=cmd, duration=duration, status=status,
                         returncode=rc, stdout="", stderr="")


# --- parse_warp_config ---

def test_parse_warp_config_defaults():
    cfg = parse_warp_config({})
    assert cfg.factor == 1.0
    assert cfg.min_duration == 0.0
    assert cfg.max_duration is None


def test_parse_warp_config_custom():
    cfg = parse_warp_config({"factor": 2.5, "min_duration": 0.1, "max_duration": 10.0})
    assert cfg.factor == 2.5
    assert cfg.min_duration == 0.1
    assert cfg.max_duration == 10.0


def test_parse_warp_config_invalid_factor():
    with pytest.raises(ValueError, match="warp factor"):
        parse_warp_config({"factor": -1})


def test_parse_warp_config_zero_factor():
    with pytest.raises(ValueError):
        parse_warp_config({"factor": 0})


# --- _warp_duration ---

def test_warp_duration_scales():
    cfg = WarpConfig(factor=2.0)
    assert _warp_duration(1.5, cfg) == pytest.approx(3.0)


def test_warp_duration_respects_min():
    cfg = WarpConfig(factor=0.1, min_duration=0.5)
    assert _warp_duration(1.0, cfg) == pytest.approx(0.5)


def test_warp_duration_respects_max():
    cfg = WarpConfig(factor=10.0, max_duration=5.0)
    assert _warp_duration(1.0, cfg) == pytest.approx(5.0)


def test_warp_duration_within_bounds():
    cfg = WarpConfig(factor=1.5, min_duration=0.0, max_duration=100.0)
    assert _warp_duration(2.0, cfg) == pytest.approx(3.0)


# --- warp_results ---

def test_warp_results_count():
    results = [make_result(duration=1.0), make_result(duration=2.0)]
    warped = warp_results(results, WarpConfig(factor=2.0))
    assert len(warped) == 2


def test_warp_results_preserves_original():
    r = make_result(duration=1.0)
    warped = warp_results([r], WarpConfig(factor=3.0))
    assert warped[0].original is r


def test_warp_results_applies_factor():
    results = [make_result(duration=4.0)]
    warped = warp_results(results, WarpConfig(factor=0.5))
    assert warped[0].warped_duration == pytest.approx(2.0)


def test_warp_results_command_and_status_forwarded():
    r = make_result(cmd="ls -la", status="failure")
    warped = warp_results([r], WarpConfig())
    assert warped[0].command == "ls -la"
    assert warped[0].status == "failure"


# --- warp_summary ---

def test_warp_summary_empty():
    s = warp_summary([])
    assert s["count"] == 0


def test_warp_summary_speedup():
    results = [make_result(duration=2.0), make_result(duration=2.0)]
    warped = warp_results(results, WarpConfig(factor=0.5))
    s = warp_summary(warped)
    assert s["total_original"] == pytest.approx(4.0)
    assert s["total_warped"] == pytest.approx(2.0)
    assert s["speedup"] == pytest.approx(2.0)
