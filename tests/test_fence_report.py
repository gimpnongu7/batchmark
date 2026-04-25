import json
import pytest
from batchmark.runner import CommandResult
from batchmark.fence import FenceConfig, FenceResult, apply_fence
from batchmark.fence_report import entry_to_dict, format_fence_json, format_fence_table


def make_result(cmd="echo hi", duration=1.0, status="success"):
    return CommandResult(
        command=cmd,
        duration=duration,
        status=status,
        stdout="",
        stderr="",
        returncode=0,
    )


@pytest.fixture
def fenced():
    results = [
        make_result(cmd="echo fast", duration=0.2, status="success"),
        make_result(cmd="echo slow", duration=8.0, status="success"),
        make_result(cmd="echo fail", duration=1.0, status="failure"),
    ]
    cfg = FenceConfig(max_duration=5.0, allow_statuses=["success"])
    return apply_fence(results, cfg)


def test_entry_to_dict_keys(fenced):
    d = entry_to_dict(fenced[0])
    assert set(d.keys()) == {"command", "duration", "status", "allowed", "reason"}


def test_entry_to_dict_allowed(fenced):
    d = entry_to_dict(fenced[0])
    assert d["allowed"] is True
    assert d["reason"] is None


def test_entry_to_dict_blocked(fenced):
    slow = fenced[1]
    d = entry_to_dict(slow)
    assert d["allowed"] is False
    assert d["reason"] is not None


def test_format_fence_json_valid(fenced):
    out = format_fence_json(fenced)
    parsed = json.loads(out)
    assert "summary" in parsed
    assert "results" in parsed
    assert parsed["summary"]["total"] == 3


def test_format_fence_json_counts(fenced):
    out = format_fence_json(fenced)
    parsed = json.loads(out)
    assert parsed["summary"]["allowed"] == 1
    assert parsed["summary"]["blocked"] == 2


def test_format_fence_table_header(fenced):
    out = format_fence_table(fenced)
    assert "Command" in out
    assert "Allowed" in out
    assert "Reason" in out


def test_format_fence_table_summary_line(fenced):
    out = format_fence_table(fenced)
    assert "Total: 3" in out
    assert "Blocked: 2" in out
