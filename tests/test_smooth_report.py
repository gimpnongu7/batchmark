"""Tests for batchmark.smooth_report."""
from __future__ import annotations

import json
import pytest

from batchmark.runner import CommandResult
from batchmark.smooth import SmoothedResult, SmoothConfig, smooth_results
from batchmark.smooth_report import (
    entry_to_dict,
    format_smooth_json,
    format_smooth_table,
    smooth_summary,
)


def make_result(cmd: str, duration: float, status: str = "success") -> CommandResult:
    return CommandResult(command=cmd, duration=duration, status=status, stdout="", stderr="", returncode=0)


@pytest.fixture
def entries():
    results = [
        make_result("echo hi", 1.0),
        make_result("echo hi", 2.0),
        make_result("echo hi", 3.0),
    ]
    return smooth_results(results, SmoothConfig(window=2))


def test_entry_to_dict_keys(entries):
    d = entry_to_dict(entries[0])
    assert set(d.keys()) == {"command", "status", "raw_duration", "smoothed_duration", "window_size"}


def test_entry_to_dict_values(entries):
    d = entry_to_dict(entries[0])
    assert d["command"] == "echo hi"
    assert d["raw_duration"] == pytest.approx(1.0)
    assert d["window_size"] == 2


def test_format_smooth_json_valid(entries):
    out = format_smooth_json(entries)
    parsed = json.loads(out)
    assert isinstance(parsed, list)
    assert len(parsed) == 3


def test_format_smooth_json_has_smoothed_key(entries):
    parsed = json.loads(format_smooth_json(entries))
    assert "smoothed_duration" in parsed[0]


def test_format_smooth_table_header(entries):
    table = format_smooth_table(entries)
    assert "Command" in table
    assert "Smooth" in table


def test_format_smooth_table_row_count(entries):
    table = format_smooth_table(entries)
    lines = [l for l in table.splitlines() if l.strip() and not l.startswith("-")]
    # header + 3 data rows
    assert len(lines) == 4


def test_format_smooth_table_empty():
    assert format_smooth_table([]) == "No smoothed results."


def test_smooth_summary_basic(entries):
    s = smooth_summary(entries)
    assert "smooth:" in s
    assert "window=2" in s


def test_smooth_summary_empty():
    assert smooth_summary([]) == "smooth: 0 results"
