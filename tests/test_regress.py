"""Tests for batchmark.regress."""
import pytest
from batchmark.runner import CommandResult
from batchmark.regress import (
    RegressConfig,
    RegressEntry,
    detect_regressions,
    parse_regress_config,
)


def make_result(cmd: str, duration: float, status: str = "success") -> CommandResult:
    return CommandResult(command=cmd, duration=duration, status=status, stdout="", stderr="", returncode=0)


@pytest.fixture
def baseline():
    return [
        make_result("echo hi", 0.10),
        make_result("echo hi", 0.12),
        make_result("sleep 0.1", 0.10),
    ]


@pytest.fixture
def current():
    return [
        make_result("echo hi", 0.25),   # regressed
        make_result("sleep 0.1", 0.11), # fine
    ]


def test_parse_regress_config_defaults():
    cfg = parse_regress_config({})
    assert cfg.threshold_pct == 10.0
    assert cfg.threshold_abs == 0.0
    assert cfg.min_baseline_runs == 1


def test_parse_regress_config_custom():
    cfg = parse_regress_config({"threshold_pct": 5.0, "threshold_abs": 0.5, "min_baseline_runs": 2})
    assert cfg.threshold_pct == 5.0
    assert cfg.threshold_abs == 0.5
    assert cfg.min_baseline_runs == 2


def test_detect_regressions_returns_entries(baseline, current):
    entries = detect_regressions(baseline, current)
    assert len(entries) == 2


def test_detect_regressions_flags_slow_command(baseline, current):
    entries = detect_regressions(baseline, current)
    by_cmd = {e.command: e for e in entries}
    assert by_cmd["echo hi"].regressed is True


def test_detect_regressions_does_not_flag_stable(baseline, current):
    entries = detect_regressions(baseline, current)
    by_cmd = {e.command: e for e in entries}
    assert by_cmd["sleep 0.1"].regressed is False


def test_detect_regressions_delta_calculation(baseline, current):
    entries = detect_regressions(baseline, current)
    by_cmd = {e.command: e for e in entries}
    e = by_cmd["echo hi"]
    assert abs(e.baseline_mean - 0.11) < 0.001
    assert abs(e.current_mean - 0.25) < 0.001
    assert abs(e.delta - (0.25 - 0.11)) < 0.001


def test_detect_regressions_skips_unknown_baseline(baseline):
    current = [make_result("new_cmd", 1.0)]
    entries = detect_regressions(baseline, current)
    assert all(e.command != "new_cmd" for e in entries)


def test_detect_regressions_min_baseline_runs_filters():
    baseline = [make_result("cmd", 0.1)]  # only 1 run
    current = [make_result("cmd", 0.5)]
    cfg = RegressConfig(min_baseline_runs=2)
    entries = detect_regressions(baseline, current, config=cfg)
    assert entries == []


def test_detect_regressions_abs_threshold():
    baseline = [make_result("cmd", 1.0)]
    current = [make_result("cmd", 1.6)]  # +0.6s, only 60% but abs > 0.5
    cfg = RegressConfig(threshold_pct=100.0, threshold_abs=0.5)
    entries = detect_regressions(baseline, current, config=cfg)
    assert entries[0].regressed is True


def test_detect_regressions_reason_contains_threshold(baseline, current):
    entries = detect_regressions(baseline, current)
    by_cmd = {e.command: e for e in entries}
    assert "%" in by_cmd["echo hi"].reason
