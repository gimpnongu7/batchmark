"""Tests for batchmark.watermark_report."""
import json
import pytest
from batchmark.runner import CommandResult
from batchmark.watermark import WatermarkConfig, WatermarkEntry, compute_watermarks
from batchmark.watermark_report import (
    format_watermark_json,
    format_watermark_table,
    watermark_summary,
)


def make_result(command: str, duration: float) -> CommandResult:
    return CommandResult(command=command, duration=duration, status="success", stdout="", stderr="", returncode=0)


@pytest.fixture
def entries():
    results = [make_result("echo hi", 0.5), make_result("sleep 1", 1.2)]
    baseline = [
        {"command": "echo hi", "high": 0.3, "low": 0.1},
        {"command": "sleep 1", "high": 2.0, "low": 1.0},
    ]
    return compute_watermarks(results, baseline=baseline, cfg=WatermarkConfig())


def test_format_watermark_json_valid(entries):
    out = format_watermark_json(entries)
    data = json.loads(out)
    assert isinstance(data, list)
    assert len(data) == 2


def test_format_watermark_json_keys(entries):
    data = json.loads(format_watermark_json(entries))
    assert "command" in data[0]
    assert "high" in data[0]
    assert "low" in data[0]
    assert "current" in data[0]


def test_format_watermark_table_header(entries):
    table = format_watermark_table(entries)
    assert "Command" in table
    assert "High" in table
    assert "Low" in table
    assert "Current" in table


def test_format_watermark_table_shows_new_high(entries):
    table = format_watermark_table(entries)
    assert "NEW HIGH" in table


def test_format_watermark_table_empty():
    out = format_watermark_table([])
    assert "No watermark data" in out


def test_watermark_summary_counts(entries):
    summary = watermark_summary(entries)
    assert "2 command(s)" in summary
    assert "1 new high(s)" in summary


def test_watermark_summary_no_breaks():
    results = [make_result("echo hi", 0.5)]
    baseline = [{"command": "echo hi", "high": 1.0, "low": 0.1}]
    entries = compute_watermarks(results, baseline=baseline, cfg=WatermarkConfig())
    summary = watermark_summary(entries)
    assert "0 new high(s)" in summary
    assert "0 new low(s)" in summary
