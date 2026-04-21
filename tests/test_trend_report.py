"""Tests for batchmark.trend_report."""
import json
import pytest
from batchmark.trend import TrendEntry
from batchmark.trend_report import (
    entry_to_dict,
    format_trend_json,
    format_trend_table,
    trend_summary,
)


def make_entry(
    cmd="echo hi",
    durations=None,
    slope=0.01,
    direction="up",
    first_mean=0.1,
    last_mean=0.2,
    pct_change=100.0,
) -> TrendEntry:
    return TrendEntry(
        command=cmd,
        durations=durations or [0.1, 0.15, 0.2],
        slope=slope,
        direction=direction,
        first_mean=first_mean,
        last_mean=last_mean,
        pct_change=pct_change,
    )


def test_entry_to_dict_keys():
    d = entry_to_dict(make_entry())
    assert set(d.keys()) == {"command", "runs", "slope", "direction", "first_mean", "last_mean", "pct_change"}


def test_entry_to_dict_values():
    d = entry_to_dict(make_entry(cmd="ls", direction="down", pct_change=-20.0))
    assert d["command"] == "ls"
    assert d["direction"] == "down"
    assert d["pct_change"] == -20.0
    assert d["runs"] == 3


def test_format_trend_json_valid():
    entries = [make_entry(), make_entry(cmd="sleep 1", direction="stable")]
    raw = format_trend_json(entries)
    parsed = json.loads(raw)
    assert len(parsed) == 2
    assert parsed[0]["command"] == "echo hi"


def test_format_trend_json_empty():
    raw = format_trend_json([])
    assert json.loads(raw) == []


def test_format_trend_table_header():
    entries = [make_entry()]
    table = format_trend_table(entries)
    assert "Command" in table
    assert "Direction" in table
    assert "Slope" in table


def test_format_trend_table_contains_arrow():
    entries = [make_entry(direction="up")]
    table = format_trend_table(entries)
    assert "↑" in table


def test_format_trend_table_empty():
    assert format_trend_table([]) == "No trend data."


def test_trend_summary_counts():
    entries = [
        make_entry(direction="up"),
        make_entry(direction="down"),
        make_entry(direction="stable"),
        make_entry(direction="up"),
    ]
    summary = trend_summary(entries)
    assert "2 slower" in summary
    assert "1 faster" in summary
    assert "1 stable" in summary
