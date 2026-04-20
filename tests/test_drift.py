"""Tests for batchmark.drift and batchmark.drift_report."""
import json
import pytest

from batchmark.drift import (
    DriftConfig,
    DriftEntry,
    detect_drift,
    parse_drift_config,
)
from batchmark.drift_report import entry_to_dict, format_drift_json, format_drift_table
from batchmark.runner import CommandResult


def make_result(command: str, duration: float, status: str = "success") -> CommandResult:
    return CommandResult(command=command, duration=duration, status=status, stdout="", stderr="", returncode=0)


@pytest.fixture
def baseline():
    return [
        make_result("echo hi", 0.1),
        make_result("sleep 1", 1.0),
        make_result("ls -la", 0.05),
    ]


@pytest.fixture
def current():
    return [
        make_result("echo hi", 0.12),   # +20% — right at threshold
        make_result("sleep 1", 1.5),    # +50% — drifted
        make_result("ls -la", 0.048),   # -4%  — fine
    ]


def test_detect_drift_returns_all_commands(baseline, current):
    entries = detect_drift(current, baseline)
    assert len(entries) == 3


def test_detect_drift_flags_slow_command(baseline, current):
    entries = detect_drift(current, baseline)
    by_cmd = {e.command: e for e in entries}
    assert by_cmd["sleep 1"].drifted is True


def test_detect_drift_no_flag_for_small_change(baseline, current):
    entries = detect_drift(current, baseline)
    by_cmd = {e.command: e for e in entries}
    assert by_cmd["ls -la"].drifted is False


def test_detect_drift_delta_calculation(baseline, current):
    entries = detect_drift(current, baseline)
    by_cmd = {e.command: e for e in entries}
    assert abs(by_cmd["sleep 1"].delta - 0.5) < 1e-9


def test_detect_drift_sorted_by_abs_pct(baseline, current):
    entries = detect_drift(current, baseline)
    pcts = [abs(e.pct_change) for e in entries]
    assert pcts == sorted(pcts, reverse=True)


def test_detect_drift_skips_missing_baseline(current):
    extra = current + [make_result("new cmd", 0.3)]
    entries = detect_drift(extra, current[:2])
    commands = [e.command for e in entries]
    assert "new cmd" not in commands


def test_parse_drift_config_defaults():
    cfg = parse_drift_config({})
    assert cfg.threshold_pct == 20.0
    assert cfg.min_baseline == 0.001


def test_parse_drift_config_custom():
    cfg = parse_drift_config({"threshold_pct": 10.0, "min_baseline": 0.01})
    assert cfg.threshold_pct == 10.0
    assert cfg.min_baseline == 0.01


def test_entry_to_dict_keys(baseline, current):
    entries = detect_drift(current, baseline)
    d = entry_to_dict(entries[0])
    assert set(d.keys()) == {"command", "current_duration", "baseline_duration", "delta", "pct_change", "drifted"}


def test_format_drift_json_valid(baseline, current):
    entries = detect_drift(current, baseline)
    out = format_drift_json(entries)
    parsed = json.loads(out)
    assert isinstance(parsed, list)
    assert len(parsed) == 3


def test_format_drift_table_header(baseline, current):
    entries = detect_drift(current, baseline)
    table = format_drift_table(entries)
    assert "Command" in table
    assert "Drift?" in table


def test_format_drift_table_summary(baseline, current):
    entries = detect_drift(current, baseline)
    table = format_drift_table(entries)
    assert "Drifted:" in table


def test_format_drift_table_empty():
    assert format_drift_table([]) == "No drift data."
