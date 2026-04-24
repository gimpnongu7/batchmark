import pytest
from batchmark.runner import CommandResult
from batchmark.jitter import (
    JitterConfig,
    JitterEntry,
    detect_jitter,
    parse_jitter_config,
)


def make_result(command: str, duration: float, status: str = "success") -> CommandResult:
    return CommandResult(
        command=command,
        duration=duration,
        returncode=0 if status == "success" else 1,
        stdout="",
        stderr="",
        status=status,
    )


# Two runs: first run is stable, second run has a spike on "slow_cmd"
run_a = [
    make_result("fast_cmd", 0.1),
    make_result("slow_cmd", 1.0),
]
run_b = [
    make_result("fast_cmd", 0.11),
    make_result("slow_cmd", 3.0),   # big spike
]


def test_detect_jitter_returns_one_entry_per_result():
    entries = detect_jitter([run_a, run_b])
    assert len(entries) == 4


def test_detect_jitter_flags_spike():
    entries = detect_jitter([run_a, run_b])
    slow_entries = [e for e in entries if e.command == "slow_cmd"]
    flagged = [e for e in slow_entries if e.flagged]
    assert len(flagged) == 1
    assert flagged[0].duration == 3.0


def test_detect_jitter_does_not_flag_stable():
    entries = detect_jitter([run_a, run_b])
    fast_entries = [e for e in entries if e.command == "fast_cmd"]
    assert all(not e.flagged for e in fast_entries)


def test_detect_jitter_reason_contains_threshold():
    entries = detect_jitter([run_a, run_b])
    flagged = [e for e in entries if e.flagged]
    assert len(flagged) == 1
    assert "threshold" in flagged[0].reason


def test_detect_jitter_mean_is_average():
    entries = detect_jitter([run_a, run_b])
    slow_entries = [e for e in entries if e.command == "slow_cmd"]
    expected_mean = (1.0 + 3.0) / 2
    for e in slow_entries:
        assert abs(e.mean - expected_mean) < 1e-9


def test_detect_jitter_insufficient_samples():
    single_run = [make_result("cmd", 0.5)]
    entries = detect_jitter([single_run], config=JitterConfig(min_samples=2))
    assert len(entries) == 1
    assert not entries[0].flagged
    assert entries[0].reason == "insufficient samples"


def test_detect_jitter_custom_threshold():
    # threshold_pct=5 should flag even small deviations
    entries = detect_jitter([run_a, run_b], config=JitterConfig(threshold_pct=5.0))
    flagged = [e for e in entries if e.flagged]
    # both fast_cmd and slow_cmd should have at least one flagged entry
    assert len(flagged) >= 2


def test_parse_jitter_config_defaults():
    cfg = parse_jitter_config({})
    assert cfg.threshold_pct == 20.0
    assert cfg.min_samples == 2


def test_parse_jitter_config_custom():
    cfg = parse_jitter_config({"threshold_pct": 10.5, "min_samples": 3})
    assert cfg.threshold_pct == 10.5
    assert cfg.min_samples == 3


def test_detect_jitter_empty_runs():
    entries = detect_jitter([])
    assert entries == []


def test_deviation_pct_zero_mean():
    # duration=0 mean=0 should not raise ZeroDivisionError
    r1 = make_result("zero_cmd", 0.0)
    r2 = make_result("zero_cmd", 0.0)
    entries = detect_jitter([[r1], [r2]])
    for e in entries:
        assert e.deviation_pct == 0.0
        assert not e.flagged
