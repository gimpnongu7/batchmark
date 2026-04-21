import json
import pytest
from batchmark.runner import CommandResult
from batchmark.histogram import HistogramConfig, HistogramBin, build_histogram
from batchmark.histogram_report import (
    bin_to_dict,
    format_histogram_json,
    format_histogram_table,
    histogram_summary,
)


def make_result(cmd: str, duration: float) -> CommandResult:
    return CommandResult(command=cmd, duration=duration, returncode=0, stdout="", stderr="", status="success")


@pytest.fixture
def bins():
    results = [
        make_result("a", 0.1),
        make_result("b", 0.4),
        make_result("c", 0.9),
    ]
    return build_histogram(results, HistogramConfig(bins=5))


def test_bin_to_dict_keys(bins):
    d = bin_to_dict(bins[0])
    assert set(d.keys()) == {"range", "low", "high", "count", "commands"}


def test_format_histogram_json_valid(bins):
    out = format_histogram_json(bins)
    parsed = json.loads(out)
    assert isinstance(parsed, list)
    assert len(parsed) == 5


def test_format_histogram_json_total_count(bins):
    out = format_histogram_json(bins)
    parsed = json.loads(out)
    total = sum(b["count"] for b in parsed)
    assert total == 3


def test_format_histogram_table_header(bins):
    table = format_histogram_table(bins)
    assert "Range" in table
    assert "Count" in table


def test_format_histogram_table_has_bars(bins):
    table = format_histogram_table(bins)
    assert "█" in table


def test_format_histogram_table_empty():
    out = format_histogram_table([])
    assert out == "(no data)"


def test_histogram_summary_total(bins):
    summary = histogram_summary(bins)
    assert "3" in summary


def test_histogram_summary_peak(bins):
    summary = histogram_summary(bins)
    assert "Peak bin" in summary
