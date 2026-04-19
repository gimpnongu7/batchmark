"""Tests for batchmark.throttle."""
from __future__ import annotations
import pytest
from dataclasses import dataclass
from typing import List
from batchmark.runner import CommandResult
from batchmark.throttle import (
    ThrottleConfig,
    parse_throttle_config,
    run_throttled,
    _should_delay,
)


def make_result(cmd: str, status: str = "success", duration: float = 0.1) -> CommandResult:
    return CommandResult(command=cmd, status=status, duration=duration, stdout="", stderr="", returncode=0)


# --- _should_delay ---

def test_no_delay_for_first_command():
    assert _should_delay(0, burst=0) is False

def test_delay_for_second_command_no_burst():
    assert _should_delay(1, burst=0) is True

def test_burst_skips_delay_within_burst():
    assert _should_delay(1, burst=3) is False
    assert _should_delay(2, burst=3) is False

def test_burst_delays_at_boundary():
    assert _should_delay(3, burst=3) is True
    assert _should_delay(6, burst=3) is True


# --- parse_throttle_config ---

def test_parse_defaults():
    cfg = parse_throttle_config({})
    assert cfg.max_concurrency == 1
    assert cfg.inter_command_delay == 0.0
    assert cfg.burst == 0

def test_parse_full():
    cfg = parse_throttle_config({"max_concurrency": 2, "inter_command_delay": 0.5, "burst": 4})
    assert cfg.max_concurrency == 2
    assert cfg.inter_command_delay == 0.5
    assert cfg.burst == 4


# --- run_throttled ---

def test_run_throttled_returns_all_results():
    cmds = ["echo a", "echo b", "echo c"]
    results = run_throttled(cmds, ThrottleConfig(), lambda c: make_result(c))
    assert len(results) == 3
    assert [r.command for r in results] == cmds

def test_run_throttled_delays_called():
    delays: List[float] = []
    cfg = ThrottleConfig(inter_command_delay=0.2)
    run_throttled(["a", "b", "c"], cfg, lambda c: make_result(c), sleep_fn=delays.append)
    assert delays == [0.2, 0.2]  # first command skipped

def test_run_throttled_no_delay_when_zero():
    delays: List[float] = []
    cfg = ThrottleConfig(inter_command_delay=0.0)
    run_throttled(["a", "b"], cfg, lambda c: make_result(c), sleep_fn=delays.append)
    assert delays == []

def test_run_throttled_burst_delays():
    delays: List[float] = []
    cfg = ThrottleConfig(inter_command_delay=0.1, burst=2)
    cmds = ["a", "b", "c", "d", "e"]
    run_throttled(cmds, cfg, lambda c: make_result(c), sleep_fn=delays.append)
    # delays at index 2 and 4
    assert len(delays) == 2

def test_run_throttled_empty_commands():
    results = run_throttled([], ThrottleConfig(), lambda c: make_result(c))
    assert results == []
