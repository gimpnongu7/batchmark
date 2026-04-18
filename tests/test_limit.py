"""Tests for batchmark.limit module."""
import time
from unittest.mock import patch, MagicMock

import pytest

from batchmark.limit import LimitConfig, _rate_delay, run_limited
from batchmark.runner import CommandResult


def make_result(cmd: str, status: str = "success", duration: float = 0.1) -> CommandResult:
    return CommandResult(command=cmd, status=status, duration=duration, stdout="", stderr="", returncode=0)


def test_rate_delay_zero():
    assert _rate_delay(0) == 0.0


def test_rate_delay_positive():
    assert _rate_delay(2) == pytest.approx(0.5)
    assert _rate_delay(4) == pytest.approx(0.25)


def test_limit_config_defaults():
    cfg = LimitConfig()
    assert cfg.max_workers == 4
    assert cfg.rate_limit == 0


def test_run_limited_returns_all_results():
    commands = ["echo a", "echo b", "echo c"]
    cfg = LimitConfig(max_workers=2)
    results = run_limited(commands, cfg)
    assert len(results) == 3
    assert all(r.status == "success" for r in results)


def test_run_limited_preserves_order():
    commands = ["echo first", "echo second", "echo third"]
    cfg = LimitConfig(max_workers=3)
    results = run_limited(commands, cfg)
    assert results[0].command == "echo first"
    assert results[1].command == "echo second"
    assert results[2].command == "echo third"


def test_run_limited_calls_on_result_callback():
    commands = ["echo x", "echo y"]
    cfg = LimitConfig(max_workers=2)
    seen = []
    run_limited(commands, cfg, on_result=seen.append)
    assert len(seen) == 2


def test_run_limited_single_worker_serializes():
    """With max_workers=1 commands run serially."""
    commands = ["echo 1", "echo 2"]
    cfg = LimitConfig(max_workers=1)
    results = run_limited(commands, cfg)
    assert len(results) == 2
    assert all(r.status == "success" for r in results)
