import pytest
from batchmark.runner import CommandResult
from batchmark.fence import (
    FenceConfig,
    FenceResult,
    parse_fence_config,
    apply_fence,
    fence_summary,
)


def make_result(cmd="echo hi", duration=1.0, status="success", stdout="", stderr="", returncode=0):
    return CommandResult(
        command=cmd,
        duration=duration,
        status=status,
        stdout=stdout,
        stderr=stderr,
        returncode=returncode,
    )


def test_parse_fence_config_defaults():
    cfg = parse_fence_config({})
    assert cfg.min_duration is None
    assert cfg.max_duration is None
    assert cfg.allow_statuses is None
    assert cfg.deny_statuses is None


def test_parse_fence_config_full():
    cfg = parse_fence_config({
        "min_duration": 0.1,
        "max_duration": 5.0,
        "allow_statuses": ["success"],
        "deny_statuses": ["timeout"],
    })
    assert cfg.min_duration == 0.1
    assert cfg.max_duration == 5.0
    assert cfg.allow_statuses == ["success"]
    assert cfg.deny_statuses == ["timeout"]


def test_apply_fence_all_allowed():
    results = [make_result(duration=1.0, status="success")]
    cfg = FenceConfig(min_duration=0.5, max_duration=2.0, allow_statuses=["success"])
    fenced = apply_fence(results, cfg)
    assert len(fenced) == 1
    assert fenced[0].allowed is True
    assert fenced[0].reason is None


def test_apply_fence_below_min():
    results = [make_result(duration=0.1)]
    cfg = FenceConfig(min_duration=0.5)
    fenced = apply_fence(results, cfg)
    assert fenced[0].allowed is False
    assert "below min" in fenced[0].reason


def test_apply_fence_above_max():
    results = [make_result(duration=10.0)]
    cfg = FenceConfig(max_duration=5.0)
    fenced = apply_fence(results, cfg)
    assert fenced[0].allowed is False
    assert "above max" in fenced[0].reason


def test_apply_fence_denied_status():
    results = [make_result(status="timeout")]
    cfg = FenceConfig(deny_statuses=["timeout"])
    fenced = apply_fence(results, cfg)
    assert fenced[0].allowed is False
    assert "denied" in fenced[0].reason


def test_apply_fence_not_in_allow_list():
    results = [make_result(status="failure")]
    cfg = FenceConfig(allow_statuses=["success"])
    fenced = apply_fence(results, cfg)
    assert fenced[0].allowed is False
    assert "not in allowed" in fenced[0].reason


def test_fence_summary_counts():
    r1 = make_result(duration=1.0, status="success")
    r2 = make_result(duration=10.0, status="success")
    cfg = FenceConfig(max_duration=5.0)
    fenced = apply_fence([r1, r2], cfg)
    summary = fence_summary(fenced)
    assert summary["total"] == 2
    assert summary["allowed"] == 1
    assert summary["blocked"] == 1


def test_fence_result_properties():
    r = make_result(cmd="ls", duration=0.5, status="success")
    fr = FenceResult(result=r, allowed=True, reason=None)
    assert fr.command == "ls"
    assert fr.duration == 0.5
    assert fr.status == "success"
