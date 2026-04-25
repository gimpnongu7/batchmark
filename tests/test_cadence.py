"""Tests for batchmark.cadence and batchmark.cadence_report."""
import json
import pytest

from batchmark.runner import CommandResult
from batchmark.cadence import (
    CadenceConfig,
    CadenceEntry,
    compute_cadence,
    cadence_summary,
    parse_cadence_config,
)
from batchmark.cadence_report import entry_to_dict, format_cadence_json, format_cadence_table


def make_result(cmd: str, duration: float, status: str = "success") -> CommandResult:
    return CommandResult(command=cmd, duration=duration, status=status, stdout="", stderr="", returncode=0)


@pytest.fixture
def sample_results():
    return [
        make_result("echo a", 0.1),
        make_result("echo b", 0.2),
        make_result("echo c", 0.05),
        make_result("echo d", 0.3, status="failure"),
    ]


def test_parse_cadence_config_defaults():
    cfg = parse_cadence_config({})
    assert cfg.late_threshold == 0.5
    assert cfg.include_failed is True


def test_parse_cadence_config_custom():
    cfg = parse_cadence_config({"late_threshold": 1.0, "include_failed": False})
    assert cfg.late_threshold == 1.0
    assert cfg.include_failed is False


def test_compute_cadence_returns_one_per_result(sample_results):
    entries = compute_cadence(sample_results)
    assert len(entries) == 4


def test_compute_cadence_first_gap_is_none(sample_results):
    entries = compute_cadence(sample_results)
    assert entries[0].gap is None


def test_compute_cadence_index_order(sample_results):
    entries = compute_cadence(sample_results)
    assert [e.index for e in entries] == [0, 1, 2, 3]


def test_compute_cadence_cumulative_increases(sample_results):
    entries = compute_cadence(sample_results)
    for i in range(1, len(entries)):
        assert entries[i].cumulative >= entries[i - 1].cumulative


def test_compute_cadence_excludes_failed_when_configured(sample_results):
    cfg = CadenceConfig(include_failed=False)
    entries = compute_cadence(sample_results, cfg)
    assert all(e.command != "echo d" for e in entries)
    assert len(entries) == 3


def test_cadence_summary_count(sample_results):
    entries = compute_cadence(sample_results)
    s = cadence_summary(entries)
    assert s["count"] == 4


def test_cadence_summary_total_duration(sample_results):
    entries = compute_cadence(sample_results)
    s = cadence_summary(entries)
    assert abs(s["total_duration"] - 0.65) < 1e-9


def test_cadence_summary_empty():
    s = cadence_summary([])
    assert s["count"] == 0
    assert s["mean_gap"] is None


def test_entry_to_dict_keys(sample_results):
    entries = compute_cadence(sample_results)
    d = entry_to_dict(entries[1])
    assert set(d.keys()) == {"index", "command", "duration", "gap", "cumulative", "is_late"}


def test_format_cadence_json_valid(sample_results):
    entries = compute_cadence(sample_results)
    out = format_cadence_json(entries)
    parsed = json.loads(out)
    assert "cadence" in parsed
    assert "summary" in parsed
    assert len(parsed["cadence"]) == 4


def test_format_cadence_table_header(sample_results):
    entries = compute_cadence(sample_results)
    table = format_cadence_table(entries)
    assert "Command" in table
    assert "Duration" in table
    assert "Gap" in table


def test_format_cadence_table_empty():
    assert format_cadence_table([]) == "No cadence data."
