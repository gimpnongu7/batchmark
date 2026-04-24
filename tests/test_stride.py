"""Tests for batchmark/stride.py."""
from __future__ import annotations

import pytest

from batchmark.runner import CommandResult
from batchmark.stride import (
    StrideConfig,
    parse_stride_config,
    stride_results,
    stride_summary,
)


def make_result(cmd: str, duration: float = 1.0, status: str = "success") -> CommandResult:
    return CommandResult(command=cmd, duration=duration, status=status, stdout="", stderr="", returncode=0)


@pytest.fixture
def sample_results():
    return [make_result(f"cmd{i}", duration=float(i)) for i in range(10)]


def test_parse_stride_config_defaults():
    cfg = parse_stride_config({})
    assert cfg.step == 1
    assert cfg.offset == 0
    assert cfg.max_results is None


def test_parse_stride_config_full():
    cfg = parse_stride_config({"step": 3, "offset": 1, "max_results": 4})
    assert cfg.step == 3
    assert cfg.offset == 1
    assert cfg.max_results == 4


def test_parse_stride_config_invalid_step():
    with pytest.raises(ValueError, match="step"):
        parse_stride_config({"step": 0})


def test_parse_stride_config_invalid_offset():
    with pytest.raises(ValueError, match="offset"):
        parse_stride_config({"offset": -1})


def test_parse_stride_config_invalid_max_results():
    with pytest.raises(ValueError, match="max_results"):
        parse_stride_config({"max_results": -5})


def test_stride_step_1_returns_all(sample_results):
    cfg = StrideConfig(step=1)
    assert stride_results(sample_results, cfg) == sample_results


def test_stride_step_2_returns_every_other(sample_results):
    cfg = StrideConfig(step=2)
    result = stride_results(sample_results, cfg)
    assert len(result) == 5
    assert result[0].command == "cmd0"
    assert result[1].command == "cmd2"


def test_stride_with_offset(sample_results):
    cfg = StrideConfig(step=2, offset=1)
    result = stride_results(sample_results, cfg)
    assert result[0].command == "cmd1"
    assert result[1].command == "cmd3"


def test_stride_max_results_limits_output(sample_results):
    cfg = StrideConfig(step=1, max_results=3)
    result = stride_results(sample_results, cfg)
    assert len(result) == 3


def test_stride_empty_list():
    cfg = StrideConfig(step=2)
    assert stride_results([], cfg) == []


def test_stride_step_larger_than_list(sample_results):
    cfg = StrideConfig(step=100)
    result = stride_results(sample_results, cfg)
    assert len(result) == 1
    assert result[0].command == "cmd0"


def test_stride_summary_format(sample_results):
    cfg = StrideConfig(step=2)
    strided = stride_results(sample_results, cfg)
    summary = stride_summary(sample_results, strided)
    assert "kept" in summary
    assert "5/10" in summary
