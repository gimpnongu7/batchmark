"""Tests verifying stats are included in report output."""
import json
import pytest
from batchmark.runner import CommandResult
from batchmark.report import results_to_dict, format_json, format_table


def make_result(cmd, exit_code=0, duration=0.5, timed_out=False):
    return CommandResult(command=cmd, exit_code=exit_code, duration=duration,
                         stdout="", stderr="", timed_out=timed_out)


@pytest.fixture
def results():
    return [
        make_result("echo hi", 0, 0.2),
        make_result("ls /tmp", 0, 0.4),
        make_result("false", 1, 0.1),
    ]


def test_results_to_dict_has_stats(results):
    d = results_to_dict(results)
    assert "stats" in d
    assert "results" in d
    assert d["stats"]["count"] == 3


def test_format_json_includes_stats(results):
    output = format_json(results)
    parsed = json.loads(output)
    assert "stats" in parsed
    assert parsed["stats"]["success_count"] == 2
    assert parsed["stats"]["failure_count"] == 1


def test_format_table_includes_summary(results):
    output = format_table(results)
    assert "Success:" in output
    assert "Failure:" in output
    assert "mean:" in output
    assert "p95:" in output


def test_format_table_row_count(results):
    output = format_table(results)
    lines = output.strip().splitlines()
    # header + separator + 3 results + separator + 2 summary lines = 8
    assert len(lines) == 8
