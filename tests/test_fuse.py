"""Tests for batchmark.fuse."""
from __future__ import annotations

import pytest

from batchmark.runner import CommandResult
from batchmark.fuse import (
    FuseConfig,
    FusedResult,
    parse_fuse_config,
    fuse_results,
)


def make_result(cmd: str, duration: float, status: str = "success") -> CommandResult:
    return CommandResult(command=cmd, duration=duration, status=status, stdout="", stderr="", returncode=0)


@pytest.fixture
def sample_results():
    return [
        make_result("echo a", 1.0),
        make_result("echo a", 2.0),
        make_result("echo b", 0.5),
        make_result("echo a", 3.0),
    ]


# --- parse_fuse_config ---

def test_parse_fuse_config_defaults():
    cfg = parse_fuse_config({})
    assert cfg.strategy == "sum"
    assert cfg.max_group is None


def test_parse_fuse_config_custom():
    cfg = parse_fuse_config({"strategy": "mean", "max_group": 3})
    assert cfg.strategy == "mean"
    assert cfg.max_group == 3


def test_parse_fuse_config_invalid_strategy():
    with pytest.raises(ValueError, match="Invalid fuse strategy"):
        parse_fuse_config({"strategy": "median"})


def test_parse_fuse_config_invalid_max_group():
    with pytest.raises(ValueError, match="max_group must be >= 1"):
        parse_fuse_config({"max_group": 0})


# --- fuse_results ---

def test_fuse_empty_returns_empty():
    assert fuse_results([], FuseConfig()) == []


def test_fuse_groups_consecutive_same_command(sample_results):
    # echo a, echo a are consecutive at start; then echo b breaks; then echo a alone
    fused = fuse_results(sample_results, FuseConfig())
    assert len(fused) == 3
    assert fused[0].command == "echo a"
    assert fused[1].command == "echo b"
    assert fused[2].command == "echo a"


def test_fuse_sum_strategy(sample_results):
    fused = fuse_results(sample_results, FuseConfig(strategy="sum"))
    assert fused[0].duration == pytest.approx(3.0)  # 1.0 + 2.0
    assert fused[2].duration == pytest.approx(3.0)  # lone echo a


def test_fuse_mean_strategy():
    results = [make_result("cmd", 1.0), make_result("cmd", 3.0)]
    fused = fuse_results(results, FuseConfig(strategy="mean"))
    assert fused[0].duration == pytest.approx(2.0)


def test_fuse_min_strategy():
    results = [make_result("cmd", 5.0), make_result("cmd", 2.0), make_result("cmd", 8.0)]
    fused = fuse_results(results, FuseConfig(strategy="min"))
    assert fused[0].duration == pytest.approx(2.0)


def test_fuse_max_strategy():
    results = [make_result("cmd", 5.0), make_result("cmd", 2.0), make_result("cmd", 8.0)]
    fused = fuse_results(results, FuseConfig(strategy="max"))
    assert fused[0].duration == pytest.approx(8.0)


def test_fuse_count_reflects_group_size(sample_results):
    fused = fuse_results(sample_results, FuseConfig())
    assert fused[0].count == 2
    assert fused[1].count == 1


def test_fuse_max_group_splits_large_groups():
    results = [make_result("cmd", float(i)) for i in range(4)]
    fused = fuse_results(results, FuseConfig(strategy="sum", max_group=2))
    assert len(fused) == 2
    assert fused[0].count == 2
    assert fused[1].count == 2


def test_fuse_failure_status_propagates():
    results = [
        make_result("cmd", 1.0, "success"),
        make_result("cmd", 1.0, "failure"),
    ]
    fused = fuse_results(results, FuseConfig())
    assert fused[0].status == "failure"


def test_fuse_sources_preserved():
    results = [make_result("cmd", 1.0), make_result("cmd", 2.0)]
    fused = fuse_results(results, FuseConfig())
    assert len(fused[0].sources) == 2
