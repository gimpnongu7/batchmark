"""Tests for batchmark.pulse."""
import pytest
from batchmark.runner import CommandResult
from batchmark.pulse import (
    PulseConfig,
    PulseEntry,
    compute_pulse,
    mean_gap,
    burst_count,
    parse_pulse_config,
)


def make_result(command: str, duration: float, status: str = "success") -> CommandResult:
    return CommandResult(
        command=command,
        duration=duration,
        status=status,
        returncode=0 if status == "success" else 1,
        stdout="",
        stderr="",
    )


@pytest.fixture
def sample_results():
    return [
        make_result("cmd_a", 0.10),
        make_result("cmd_b", 0.12),
        make_result("cmd_c", 0.50),
        make_result("cmd_d", 0.51),
        make_result("cmd_e", 1.00, status="failure"),
    ]


def test_parse_pulse_config_defaults():
    cfg = parse_pulse_config({})
    assert cfg.burst_threshold == 0.05
    assert cfg.include_failures is True


def test_parse_pulse_config_custom():
    cfg = parse_pulse_config({"burst_threshold": 0.1, "include_failures": False})
    assert cfg.burst_threshold == 0.1
    assert cfg.include_failures is False


def test_compute_pulse_returns_one_per_result(sample_results):
    entries = compute_pulse(sample_results)
    assert len(entries) == len(sample_results)


def test_first_entry_has_no_gap(sample_results):
    entries = compute_pulse(sample_results)
    assert entries[0].gap is None
    assert entries[0].is_burst is False


def test_subsequent_entries_have_gap(sample_results):
    entries = compute_pulse(sample_results)
    for e in entries[1:]:
        assert e.gap is not None


def test_burst_detected_for_small_gap(sample_results):
    cfg = PulseConfig(burst_threshold=0.05)
    entries = compute_pulse(sample_results, config=cfg)
    # gap between cmd_c (0.50) and cmd_d (0.51) is 0.01 -> burst
    assert entries[3].is_burst is True


def test_large_gap_not_burst(sample_results):
    cfg = PulseConfig(burst_threshold=0.05)
    entries = compute_pulse(sample_results, config=cfg)
    # gap between cmd_b (0.12) and cmd_c (0.50) is 0.38 -> not burst
    assert entries[2].is_burst is False


def test_include_failures_false_excludes_failures(sample_results):
    cfg = PulseConfig(include_failures=False)
    entries = compute_pulse(sample_results, config=cfg)
    statuses = [e.status for e in entries]
    assert "failure" not in statuses
    assert len(entries) == 4


def test_mean_gap_none_when_single_entry():
    results = [make_result("only", 0.5)]
    entries = compute_pulse(results)
    assert mean_gap(entries) is None


def test_mean_gap_computed_correctly(sample_results):
    entries = compute_pulse(sample_results)
    gaps = [e.gap for e in entries if e.gap is not None]
    expected = sum(gaps) / len(gaps)
    assert abs(mean_gap(entries) - expected) < 1e-9


def test_burst_count_zero_when_threshold_zero(sample_results):
    cfg = PulseConfig(burst_threshold=0.0)
    entries = compute_pulse(sample_results, config=cfg)
    assert burst_count(entries) == 0


def test_index_is_sequential(sample_results):
    entries = compute_pulse(sample_results)
    for i, e in enumerate(entries):
        assert e.index == i
