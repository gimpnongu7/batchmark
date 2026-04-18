"""Tests for CLI export helper."""
import pytest
from batchmark.runner import CommandResult
from batchmark.cli_export import infer_format, handle_export


def make_result(cmd="echo hi", status="success", duration=0.1, rc=0):
    return CommandResult(
        command=cmd, status=status, duration=duration,
        returncode=rc, stdout="", stderr="",
    )


def test_infer_format_csv():
    assert infer_format("results.csv") == "csv"


def test_infer_format_md():
    assert infer_format("report.md") == "markdown"


def test_infer_format_markdown_ext():
    assert infer_format("report.markdown") == "markdown"


def test_infer_format_unknown_raises():
    with pytest.raises(ValueError, match="Cannot infer export format"):
        infer_format("report.html")


def test_handle_export_no_path_does_nothing(tmp_path):
    # Should not raise or create any file
    handle_export([make_result()], None, None)


def test_handle_export_csv(tmp_path, capsys):
    p = tmp_path / "out.csv"
    handle_export([make_result()], str(p), "csv")
    assert p.exists()
    captured = capsys.readouterr()
    assert "Exported" in captured.out


def test_handle_export_infers_fmt_from_path(tmp_path):
    p = tmp_path / "out.md"
    handle_export([make_result()], str(p), None)
    assert p.exists()


def test_handle_export_invalid_fmt_raises(tmp_path):
    p = tmp_path / "out.csv"
    with pytest.raises(ValueError, match="Unsupported export format"):
        handle_export([make_result()], str(p), "xml")
