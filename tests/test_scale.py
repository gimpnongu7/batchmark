"""Tests for batchmark.scale."""
from __future__ import annotations

import pytest

from batchmark.runner import CommandResult
from batchmark.scale import (
    ScaleConfig,
    ScaledResult,
    parse_scale_config,
    scale_results,
    scale_summary,
)


def make_result(command: str = "echo hi", duration: float = 1.0, status: str = "success") -> CommandResult:
    return CommandResult(
        command=command,
        returncode=0 if status == "success" else 1,
        stdout="",
        stderr="",
        duration=duration,
        status=status,
    )


@pytest.fixture
def sample_results():
    return [
        make_result("cmd_a", 2.0),
        make_result("cmd_b", 4.0),
        make_result("cmd_c", 1.0, status="failure"),
    ]


def test_parse_scale_config_defaults():
    cfg = parse_scale_config({})
    assert cfg.factor == 1.0
    assert cfg.per_command == {}
    assert cfg.min_duration == 0.0


def test_parse_scale_config_custom():
    cfg = parse_scale_config({"factor": 2.5, "per_command": {"cmd_a": 0.5}, "min_duration": 0.1})
    assert cfg.factor == 2.5
    assert cfg.per_command == {"cmd_a": 0.5}
    assert cfg.min_duration == 0.1


def test_parse_scale_config_invalid_factor():
    with pytest.raises(ValueError, match="factor must be positive"):
        ScaleConfig(factor=0.0)


def test_parse_scale_config_negative_min_duration():
    with pytest.raises(ValueError, match="min_duration must be"):
        ScaleConfig(min_duration=-1.0)


def test_scale_results_returns_one_per_input(sample_results):
    out = scale_results(sample_results)
    assert len(out) == len(sample_results)


def test_scale_results_global_factor(sample_results):
    cfg = ScaleConfig(factor=2.0)
    out = scale_results(sample_results, cfg)
    assert out[0].duration == pytest.approx(4.0)
    assert out[1].duration == pytest.approx(8.0)


def test_scale_results_per_command_overrides_global(sample_results):
    cfg = ScaleConfig(factor=2.0, per_command={"cmd_a": 0.5})
    out = scale_results(sample_results, cfg)
    assert out[0].duration == pytest.approx(1.0)   # 2.0 * 0.5
    assert out[1].duration == pytest.approx(8.0)   # 4.0 * 2.0


def test_scale_results_respects_min_duration(sample_results):
    cfg = ScaleConfig(factor=0.001, min_duration=0.5)
    out = scale_results(sample_results, cfg)
    for s in out:
        assert s.duration >= 0.5


def test_scale_results_preserves_raw_duration(sample_results):
    cfg = ScaleConfig(factor=3.0)
    out = scale_results(sample_results, cfg)
    assert out[0].raw_duration == pytest.approx(2.0)
    assert out[1].raw_duration == pytest.approx(4.0)


def test_scale_results_preserves_status(sample_results):
    out = scale_results(sample_results)
    statuses = [s.status for s in out]
    assert statuses == ["success", "success", "failure"]


def test_scale_summary_empty():
    summary = scale_summary([])
    assert summary["count"] == 0
    assert summary["total_raw"] == 0.0


def test_scale_summary_values(sample_results):
    cfg = ScaleConfig(factor=2.0)
    out = scale_results(sample_results, cfg)
    summary = scale_summary(out)
    assert summary["count"] == 3
    assert summary["total_raw"] == pytest.approx(7.0)
    assert summary["total_scaled"] == pytest.approx(14.0)
    assert summary["ratio"] == pytest.approx(2.0)
