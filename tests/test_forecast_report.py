"""Tests for batchmark.forecast_report."""
import json
import pytest
from batchmark.forecast import ForecastEntry
from batchmark.forecast_report import (
    entry_to_dict,
    format_forecast_json,
    format_forecast_table,
)


def make_entry(cmd="echo hi", samples=3, mean=1.0, predicted=1.0, trend="stable"):
    return ForecastEntry(
        command=cmd,
        sample_count=samples,
        mean_duration=mean,
        predicted_next=predicted,
        trend=trend,
    )


def test_entry_to_dict_keys():
    d = entry_to_dict(make_entry())
    assert set(d.keys()) == {"command", "sample_count", "mean_duration", "predicted_next", "trend"}


def test_entry_to_dict_values():
    d = entry_to_dict(make_entry(cmd="ls", samples=5, mean=0.42, predicted=0.44, trend="degrading"))
    assert d["command"] == "ls"
    assert d["sample_count"] == 5
    assert d["mean_duration"] == 0.42
    assert d["trend"] == "degrading"


def test_format_forecast_json_valid():
    entries = [make_entry(trend="improving"), make_entry(cmd="sleep 1", trend="degrading")]
    out = format_forecast_json(entries)
    parsed = json.loads(out)
    assert len(parsed) == 2
    assert parsed[0]["trend"] == "improving"


def test_format_forecast_table_header():
    entries = [make_entry()]
    table = format_forecast_table(entries)
    assert "Command" in table
    assert "Predicted" in table
    assert "Trend" in table


def test_format_forecast_table_row_content():
    entries = [make_entry(cmd="ping", mean=2.5, predicted=2.6, trend="degrading")]
    table = format_forecast_table(entries)
    assert "ping" in table
    assert "degrading" in table


def test_format_forecast_table_empty():
    assert format_forecast_table([]) == "No forecast data."


def test_format_forecast_table_long_command_truncated():
    long_cmd = "x" * 50
    entries = [make_entry(cmd=long_cmd)]
    table = format_forecast_table(entries)
    assert "..." in table
