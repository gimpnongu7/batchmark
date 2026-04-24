"""Tests for batchmark.velocity_report."""
import json
import pytest
from batchmark.velocity import VelocityEntry, VelocityConfig, compute_velocity
from batchmark.runner import CommandResult
from batchmark.velocity_report import (
    entry_to_dict,
    format_velocity_json,
    format_velocity_table,
    velocity_summary,
)


def make_result(cmd: str, duration: float) -> CommandResult:
    return CommandResult(command=cmd, duration=duration, returncode=0, stdout="", stderr="", status="success")


@pytest.fixture
def entries():
    results = [make_result(f"cmd_{i}", float(i + 1)) for i in range(4)]
    return compute_velocity(results, VelocityConfig(min_samples=2, window=3))


def test_entry_to_dict_keys(entries):
    d = entry_to_dict(entries[2])
    assert set(d.keys()) == {"index", "command", "duration", "rolling_velocity", "cumulative_velocity", "accelerating"}


def test_entry_to_dict_none_for_early(entries):
    d = entry_to_dict(entries[0])
    assert d["rolling_velocity"] is None
    assert d["cumulative_velocity"] is None


def test_entry_to_dict_values_present(entries):
    d = entry_to_dict(entries[2])
    assert d["rolling_velocity"] is not None
    assert d["cumulative_velocity"] is not None


def test_format_velocity_json_valid(entries):
    out = format_velocity_json(entries)
    parsed = json.loads(out)
    assert isinstance(parsed, list)
    assert len(parsed) == len(entries)


def test_format_velocity_json_has_index(entries):
    parsed = json.loads(format_velocity_json(entries))
    assert parsed[0]["index"] == 0
    assert parsed[-1]["index"] == len(entries) - 1


def test_format_velocity_table_header(entries):
    table = format_velocity_table(entries)
    assert "Rolling v/s" in table
    assert "Cumul v/s" in table


def test_format_velocity_table_row_count(entries):
    lines = format_velocity_table(entries).splitlines()
    # header + separator + N data rows
    assert len(lines) == 2 + len(entries)


def test_velocity_summary_contains_cmd_s(entries):
    s = velocity_summary(entries)
    assert "cmd/s" in s


def test_velocity_summary_empty():
    s = velocity_summary([])
    assert "No velocity" in s
