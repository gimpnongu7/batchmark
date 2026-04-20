"""Tests for batchmark.prune and batchmark.prune_report."""
import json
import pytest

from batchmark.runner import CommandResult
from batchmark.prune import (
    PruneConfig,
    parse_prune_config,
    prune_results,
    prune_summary,
)
from batchmark.prune_report import format_prune_json, format_prune_table


def make_result(command: str, status: str = "success", duration: float = 1.0) -> CommandResult:
    return CommandResult(command=command, status=status, duration=duration, stdout="", stderr="")


@pytest.fixture()
def sample_results():
    return [
        make_result("cmd_a", "success", 0.5),
        make_result("cmd_b", "failure", 2.0),
        make_result("cmd_c", "success", 1.5),
        make_result("cmd_d", "timeout", 5.0),
        make_result("cmd_e", "success", 0.8),
    ]


def test_parse_prune_config_defaults():
    cfg = parse_prune_config({})
    assert cfg.keep_last is None
    assert cfg.drop_status is None
    assert cfg.min_duration is None
    assert cfg.max_duration is None


def test_parse_prune_config_full():
    cfg = parse_prune_config(
        {"keep_last": 3, "drop_status": "failure", "min_duration": 0.5, "max_duration": 4.0}
    )
    assert cfg.keep_last == 3
    assert cfg.drop_status == "failure"
    assert cfg.min_duration == 0.5
    assert cfg.max_duration == 4.0


def test_prune_drop_status(sample_results):
    cfg = PruneConfig(drop_status="success")
    result = prune_results(sample_results, cfg)
    statuses = [r.status for r in result]
    assert "success" not in statuses
    assert len(result) == 2


def test_prune_min_duration(sample_results):
    cfg = PruneConfig(min_duration=1.0)
    result = prune_results(sample_results, cfg)
    assert all(r.duration >= 1.0 for r in result)


def test_prune_max_duration(sample_results):
    cfg = PruneConfig(max_duration=2.0)
    result = prune_results(sample_results, cfg)
    assert all(r.duration <= 2.0 for r in result)


def test_prune_keep_last(sample_results):
    cfg = PruneConfig(keep_last=2)
    result = prune_results(sample_results, cfg)
    assert len(result) == 2
    assert result[-1].command == "cmd_e"


def test_prune_keep_last_zero(sample_results):
    cfg = PruneConfig(keep_last=0)
    result = prune_results(sample_results, cfg)
    assert result == []


def test_prune_combined(sample_results):
    cfg = PruneConfig(drop_status="timeout", max_duration=2.0, keep_last=2)
    result = prune_results(sample_results, cfg)
    assert all(r.status != "timeout" for r in result)
    assert all(r.duration <= 2.0 for r in result)
    assert len(result) <= 2


def test_prune_summary_counts(sample_results):
    cfg = PruneConfig(drop_status="success")
    pruned = prune_results(sample_results, cfg)
    summary = prune_summary(sample_results, pruned)
    assert summary["original_count"] == 5
    assert summary["pruned_count"] == 2
    assert summary["removed_count"] == 3


def test_format_prune_json_valid(sample_results):
    cfg = PruneConfig(drop_status="failure")
    pruned = prune_results(sample_results, cfg)
    out = format_prune_json(sample_results, pruned, cfg)
    data = json.loads(out)
    assert "summary" in data
    assert "results" in data
    assert data["summary"]["removed_count"] == 1


def test_format_prune_table_header(sample_results):
    cfg = PruneConfig(keep_last=3)
    pruned = prune_results(sample_results, cfg)
    out = format_prune_table(sample_results, pruned)
    assert "Pruned" in out
    assert "Command" in out
    assert "Duration" in out
