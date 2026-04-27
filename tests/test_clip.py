"""Tests for batchmark.clip and batchmark.clip_report."""
import json
import pytest

from batchmark.runner import CommandResult
from batchmark.clip import (
    ClipConfig,
    parse_clip_config,
    clip_results,
    clip_summary,
)
from batchmark.clip_report import format_clip_json, format_clip_table


def make_result(cmd: str, status: str = "success", duration: float = 1.0) -> CommandResult:
    rc = 0 if status == "success" else 1
    return CommandResult(command=cmd, status=status, duration=duration,
                         returncode=rc, stdout="", stderr="")


@pytest.fixture
def sample_results():
    return [
        make_result("cmd_a", "success", 0.5),
        make_result("cmd_b", "success", 1.0),
        make_result("cmd_c", "failure", 2.0),
        make_result("cmd_d", "success", 0.8),
        make_result("cmd_e", "failure", 1.5),
    ]


def test_parse_clip_config_defaults():
    cfg = parse_clip_config({})
    assert cfg.max_per_status == {}
    assert cfg.max_total is None
    assert cfg.keep == "first"


def test_parse_clip_config_full():
    cfg = parse_clip_config({"max_per_status": {"success": 2}, "max_total": 4, "keep": "last"})
    assert cfg.max_per_status == {"success": 2}
    assert cfg.max_total == 4
    assert cfg.keep == "last"


def test_parse_clip_config_invalid_keep():
    with pytest.raises(ValueError, match="keep"):
        parse_clip_config({"keep": "random"})


def test_parse_clip_config_invalid_max_total():
    with pytest.raises(ValueError, match="max_total"):
        parse_clip_config({"max_total": 0})


def test_parse_clip_config_invalid_per_status():
    with pytest.raises(ValueError):
        parse_clip_config({"max_per_status": {"success": 0}})


def test_clip_per_status_limits(sample_results):
    cfg = ClipConfig(max_per_status={"success": 2, "failure": 1})
    out = clip_results(sample_results, cfg)
    success_count = sum(1 for r in out if r.status == "success")
    failure_count = sum(1 for r in out if r.status == "failure")
    assert success_count == 2
    assert failure_count == 1


def test_clip_max_total(sample_results):
    cfg = ClipConfig(max_total=3)
    out = clip_results(sample_results, cfg)
    assert len(out) == 3


def test_clip_keep_last(sample_results):
    cfg = ClipConfig(max_per_status={"success": 1}, keep="last")
    out = clip_results(sample_results, cfg)
    success_results = [r for r in out if r.status == "success"]
    assert len(success_results) == 1
    assert success_results[0].command == "cmd_d"


def test_clip_no_limits(sample_results):
    cfg = ClipConfig()
    out = clip_results(sample_results, cfg)
    assert len(out) == len(sample_results)


def test_clip_summary(sample_results):
    cfg = ClipConfig(max_total=3)
    clipped = clip_results(sample_results, cfg)
    s = clip_summary(sample_results, clipped)
    assert s["original_count"] == 5
    assert s["clipped_count"] == 3
    assert s["dropped"] == 2


def test_format_clip_json(sample_results):
    cfg = ClipConfig(max_total=2)
    out = format_clip_json(sample_results, cfg)
    data = json.loads(out)
    assert "summary" in data
    assert "results" in data
    assert data["summary"]["clipped_count"] == 2
    assert len(data["results"]) == 2


def test_format_clip_table(sample_results):
    cfg = ClipConfig(max_total=2)
    table = format_clip_table(sample_results, cfg)
    assert "Clip summary" in table
    assert "kept" in table
    assert "dropped" in table
