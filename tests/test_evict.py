"""Tests for batchmark/evict.py"""
import pytest
from batchmark.runner import CommandResult
from batchmark.evict import (
    EvictConfig,
    parse_evict_config,
    evict_results,
    evict_summary,
)


def make_result(cmd: str, status: str = "success", duration: float = 1.0) -> CommandResult:
    return CommandResult(command=cmd, status=status, duration=duration, stdout="", stderr="", returncode=0)


@pytest.fixture
def sample_results():
    return [
        make_result("echo a", "success", 0.5),
        make_result("echo b", "failure", 1.5),
        make_result("echo c", "timeout", 10.0),
        make_result("echo d", "success", 2.0),
        make_result("echo e", "success", 0.3),
    ]


def test_parse_evict_config_defaults():
    cfg = parse_evict_config({})
    assert cfg.max_results is None
    assert cfg.max_duration is None
    assert cfg.drop_failures is False
    assert cfg.drop_timeouts is False


def test_parse_evict_config_full():
    cfg = parse_evict_config(
        {"max_results": 10, "max_duration": 5.0, "drop_failures": True, "drop_timeouts": True}
    )
    assert cfg.max_results == 10
    assert cfg.max_duration == 5.0
    assert cfg.drop_failures is True
    assert cfg.drop_timeouts is True


def test_evict_drop_failures(sample_results):
    cfg = EvictConfig(drop_failures=True)
    kept = evict_results(sample_results, cfg)
    assert all(r.status == "success" for r in kept)
    assert len(kept) == 3


def test_evict_drop_timeouts(sample_results):
    cfg = EvictConfig(drop_timeouts=True)
    kept = evict_results(sample_results, cfg)
    assert not any(r.status == "timeout" for r in kept)
    assert len(kept) == 4


def test_evict_max_duration(sample_results):
    cfg = EvictConfig(max_duration=1.0)
    kept = evict_results(sample_results, cfg)
    assert all(r.duration <= 1.0 for r in kept)


def test_evict_max_results_keeps_most_recent(sample_results):
    cfg = EvictConfig(max_results=3)
    kept = evict_results(sample_results, cfg)
    assert len(kept) == 3
    assert kept[-1].command == "echo e"


def test_evict_combined_rules(sample_results):
    cfg = EvictConfig(drop_timeouts=True, max_duration=1.5, max_results=2)
    kept = evict_results(sample_results, cfg)
    assert len(kept) <= 2
    assert not any(r.status == "timeout" for r in kept)
    assert all(r.duration <= 1.5 for r in kept)


def test_evict_no_rules_returns_all(sample_results):
    cfg = EvictConfig()
    kept = evict_results(sample_results, cfg)
    assert len(kept) == len(sample_results)


def test_evict_summary_counts(sample_results):
    cfg = EvictConfig(drop_failures=True)
    kept = evict_results(sample_results, cfg)
    summary = evict_summary(sample_results, kept)
    assert summary["original_count"] == 5
    assert summary["remaining_count"] == 3
    assert summary["evicted_count"] == 2
