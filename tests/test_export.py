"""Tests for batchmark/export.py"""
import os
import csv
import io
import pytest
from batchmark.runner import CommandResult
from batchmark.export import format_csv, format_markdown, write_export


def make_result(cmd, status, duration, rc=0):
    return CommandResult(
        command=cmd,
        status=status,
        duration=duration,
        returncode=rc,
        stdout="",
        stderr="",
    )


@pytest.fixture
def sample_results():
    return [
        make_result("echo hi", "success", 0.1),
        make_result("false", "failure", 0.05, rc=1),
        make_result("sleep 0.01", "success", 0.01),
    ]


def test_format_csv_header(sample_results):
    out = format_csv(sample_results)
    reader = csv.reader(io.StringIO(out))
    header = next(reader)
    assert header == ["command", "status", "duration", "returncode", "stdout", "stderr"]


def test_format_csv_row_count(sample_results):
    out = format_csv(sample_results)
    rows = list(csv.reader(io.StringIO(out)))
    assert len(rows) == len(sample_results) + 1  # header + data


def test_format_csv_values(sample_results):
    out = format_csv(sample_results)
    rows = list(csv.reader(io.StringIO(out)))
    assert rows[1][0] == "echo hi"
    assert rows[1][1] == "success"
    assert rows[2][3] == "1"  # returncode for false


def test_format_markdown_contains_header(sample_results):
    out = format_markdown(sample_results)
    assert "| Command |" in out
    assert "|---------|" in out


def test_format_markdown_contains_commands(sample_results):
    out = format_markdown(sample_results)
    assert "`echo hi`" in out
    assert "`false`" in out


def test_format_markdown_contains_stats(sample_results):
    out = format_markdown(sample_results)
    assert "**Total:**" in out
    assert "**Passed:**" in out
    assert "**Failed:**" in out


def test_write_export_csv(tmp_path, sample_results):
    p = tmp_path / "out.csv"
    write_export(sample_results, str(p), "csv")
    assert p.exists()
    content = p.read_text()
    assert "echo hi" in content


def test_write_export_markdown(tmp_path, sample_results):
    p = tmp_path / "out.md"
    write_export(sample_results, str(p), "markdown")
    assert p.exists()
    content = p.read_text()
    assert "**Total:**" in content


def test_write_export_invalid_format(tmp_path, sample_results):
    with pytest.raises(ValueError, match="Unsupported export format"):
        write_export(sample_results, str(tmp_path / "out.txt"), "xml")
