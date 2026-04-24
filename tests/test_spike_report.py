"""Tests for batchmark.spike_report."""
import json
import pytest
from batchmark.runner import CommandResult
from batchmark.spike import SpikeEntry, detect_spikes, SpikeConfig
from batchmark.spike_report import (
    entry_to_dict,
    format_spike_json,
    format_spike_table,
    spike_summary,
)


def make_result(cmd: str, duration: float, status: str = "success") -> CommandResult:
    return CommandResult(command=cmd, duration=duration, status=status, stdout="", stderr="", returncode=0)


@pytest.fixture
def entries():
    base = [make_result(f"cmd{i}", 1.0) for i in range(5)]
    spike = make_result("spike_cmd", 9.0)
    cfg = SpikeConfig(threshold=2.0, min_samples=3, window=10)
    return detect_spikes(base + [spike], cfg)


@pytest.fixture
def no_spike_entries():
    """All results are uniform, so no spikes should be detected."""
    base = [make_result(f"cmd{i}", 1.0) for i in range(6)]
    cfg = SpikeConfig(threshold=2.0, min_samples=3, window=10)
    return detect_spikes(base, cfg)


def test_entry_to_dict_keys(entries):
    d = entry_to_dict(entries[0])
    assert set(d.keys()) == {"command", "duration", "status", "rolling_mean", "ratio", "is_spike"}


def test_entry_to_dict_spike_flagged(entries):
    last = entry_to_dict(entries[-1])
    assert last["is_spike"] is True
    assert last["ratio"] is not None


def test_entry_to_dict_no_rolling_mean_early(entries):
    early = entry_to_dict(entries[0])
    assert early["rolling_mean"] is None
    assert early["ratio"] is None


def test_format_spike_json_valid(entries):
    output = format_spike_json(entries)
    parsed = json.loads(output)
    assert isinstance(parsed, list)
    assert len(parsed) == len(entries)


def test_format_spike_json_spike_present(entries):
    output = format_spike_json(entries)
    parsed = json.loads(output)
    spikes = [e for e in parsed if e["is_spike"]]
    assert len(spikes) == 1
    assert spikes[0]["command"] == "spike_cmd"


def test_format_spike_table_header(entries):
    table = format_spike_table(entries)
    assert "Command" in table
    assert "Duration" in table
    assert "Spike" in table


def test_format_spike_table_flags_spike(entries):
    table = format_spike_table(entries)
    assert "YES" in table


def test_spike_summary_counts(entries):
    summary = spike_summary(entries)
    assert "1/6" in summary
    assert "spike" in summary.lower()


def test_spike_summary_no_spikes(no_spike_entries):
    """spike_summary should report 0 spikes when none are detected."""
    summary = spike_summary(no_spike_entries)
    assert "0/" in summary
    assert "spike" in summary.lower()


def test_format_spike_table_no_yes_when_no_spikes(no_spike_entries):
    """Table should not contain YES if there are no spikes."""
    table = format_spike_table(no_spike_entries)
    assert "YES" not in table
