"""Tests for batchmark.watermark."""
import pytest
from batchmark.runner import CommandResult
from batchmark.watermark import (
    WatermarkConfig,
    compute_watermarks,
    parse_watermark_config,
    watermarks_to_dicts,
)


def make_result(command: str, duration: float, status: str = "success") -> CommandResult:
    return CommandResult(command=command, duration=duration, status=status, stdout="", stderr="", returncode=0)


@pytest.fixture
def results():
    return [
        make_result("echo hi", 0.5),
        make_result("sleep 1", 1.2),
    ]


def test_parse_watermark_config_defaults():
    cfg = parse_watermark_config({})
    assert cfg.track == "both"
    assert cfg.metric == "duration"


def test_parse_watermark_config_custom():
    cfg = parse_watermark_config({"track": "high", "metric": "duration"})
    assert cfg.track == "high"


def test_no_baseline_sets_current_as_watermark(results):
    cfg = WatermarkConfig()
    entries = compute_watermarks(results, baseline=None, cfg=cfg)
    assert len(entries) == 2
    assert entries[0].high == pytest.approx(0.5)
    assert entries[0].low == pytest.approx(0.5)


def test_high_broken_when_current_exceeds_baseline(results):
    baseline = [{"command": "echo hi", "high": 0.3, "low": 0.1}]
    cfg = WatermarkConfig()
    entries = compute_watermarks(results, baseline=baseline, cfg=cfg)
    echo_entry = next(e for e in entries if e.command == "echo hi")
    assert echo_entry.high_broken is True
    assert echo_entry.high == pytest.approx(0.5)


def test_low_broken_when_current_beats_baseline(results):
    baseline = [{"command": "echo hi", "high": 1.0, "low": 0.8}]
    cfg = WatermarkConfig()
    entries = compute_watermarks(results, baseline=baseline, cfg=cfg)
    echo_entry = next(e for e in entries if e.command == "echo hi")
    assert echo_entry.low_broken is True
    assert echo_entry.low == pytest.approx(0.5)


def test_no_break_when_within_range(results):
    baseline = [{"command": "echo hi", "high": 1.0, "low": 0.1}]
    cfg = WatermarkConfig()
    entries = compute_watermarks(results, baseline=baseline, cfg=cfg)
    echo_entry = next(e for e in entries if e.command == "echo hi")
    assert echo_entry.high_broken is False
    assert echo_entry.low_broken is False


def test_track_high_only_omits_low(results):
    cfg = WatermarkConfig(track="high")
    entries = compute_watermarks(results, baseline=None, cfg=cfg)
    assert entries[0].low is None
    assert entries[0].high is not None


def test_track_low_only_omits_high(results):
    cfg = WatermarkConfig(track="low")
    entries = compute_watermarks(results, baseline=None, cfg=cfg)
    assert entries[0].high is None
    assert entries[0].low is not None


def test_watermarks_to_dicts_keys(results):
    cfg = WatermarkConfig()
    entries = compute_watermarks(results, baseline=None, cfg=cfg)
    d = watermarks_to_dicts(entries)
    assert set(d[0].keys()) == {"command", "current", "high", "low", "high_broken", "low_broken"}


def test_unknown_command_in_results_gets_no_baseline():
    r = [make_result("new cmd", 0.9)]
    baseline = [{"command": "old cmd", "high": 0.5, "low": 0.1}]
    cfg = WatermarkConfig()
    entries = compute_watermarks(r, baseline=baseline, cfg=cfg)
    assert entries[0].high_broken is False
    assert entries[0].low_broken is False
