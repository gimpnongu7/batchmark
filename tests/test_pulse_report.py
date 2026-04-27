"""Tests for batchmark.pulse_report."""
import json
import pytest
from batchmark.runner import CommandResult
from batchmark.pulse import compute_pulse, PulseConfig
from batchmark.pulse_report import (
    entry_to_dict,
    format_pulse_json,
    format_pulse_table,
    pulse_summary,
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
def entries():
    results = [
        make_result("alpha", 0.10),
        make_result("beta", 0.11),
        make_result("gamma", 0.80),
    ]
    return compute_pulse(results, config=PulseConfig(burst_threshold=0.05))


def test_entry_to_dict_keys(entries):
    d = entry_to_dict(entries[0])
    assert set(d.keys()) == {"index", "command", "duration", "status", "gap", "is_burst"}


def test_entry_to_dict_first_gap_is_none(entries):
    d = entry_to_dict(entries[0])
    assert d["gap"] is None
    assert d["is_burst"] is False


def test_entry_to_dict_subsequent_gap_present(entries):
    d = entry_to_dict(entries[1])
    assert d["gap"] is not None


def test_format_pulse_json_valid(entries):
    output = format_pulse_json(entries)
    parsed = json.loads(output)
    assert "pulse" in parsed
    assert "summary" in parsed
    assert len(parsed["pulse"]) == len(entries)


def test_format_pulse_json_summary_keys(entries):
    parsed = json.loads(format_pulse_json(entries))
    summary = parsed["summary"]
    assert "total" in summary
    assert "burst_count" in summary
    assert "mean_gap" in summary


def test_format_pulse_table_header(entries):
    table = format_pulse_table(entries)
    assert "Command" in table
    assert "Duration" in table
    assert "Gap" in table
    assert "Burst" in table


def test_format_pulse_table_row_count(entries):
    table = format_pulse_table(entries)
    lines = [l for l in table.splitlines() if not l.startswith("-") and l.strip()]
    # header + data rows + summary line
    assert len(lines) >= len(entries) + 1


def test_pulse_summary_total(entries):
    s = pulse_summary(entries)
    assert s["total"] == len(entries)


def test_pulse_summary_burst_count_type(entries):
    s = pulse_summary(entries)
    assert isinstance(s["burst_count"], int)
