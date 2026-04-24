"""Tests for batchmark.cushion."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pytest

from batchmark.cushion import (
    CushionConfig,
    CushionState,
    parse_cushion_config,
    run_cushioned,
)
from batchmark.runner import CommandResult


def make_result(cmd: str, duration: float, status: str = "success") -> CommandResult:
    return CommandResult(command=cmd, duration=duration, status=status, stdout="", stderr="", returncode=0)


# --- CushionConfig defaults ---

def test_parse_cushion_config_defaults():
    cfg = parse_cushion_config({})
    assert cfg.base_seconds == 0.0
    assert cfg.variance_factor == 0.1
    assert cfg.window == 5
    assert cfg.max_seconds == 10.0
    assert cfg.enabled is True


def test_parse_cushion_config_custom():
    cfg = parse_cushion_config({"cushion": {"base_seconds": 1.5, "window": 3, "enabled": False}})
    assert cfg.base_seconds == 1.5
    assert cfg.window == 3
    assert cfg.enabled is False


# --- CushionState stddev / cushion_seconds ---

def test_cushion_seconds_no_history():
    state = CushionState(config=CushionConfig(base_seconds=0.2))
    assert state.cushion_seconds() == pytest.approx(0.2)


def test_cushion_seconds_disabled():
    state = CushionState(config=CushionConfig(base_seconds=5.0, enabled=False))
    assert state.cushion_seconds() == 0.0


def test_cushion_seconds_with_variance():
    cfg = CushionConfig(base_seconds=0.0, variance_factor=1.0, window=4)
    state = CushionState(config=cfg)
    for d in [1.0, 3.0, 1.0, 3.0]:
        state.record(make_result("cmd", d))
    # mean=2.0, variance=1.0, stddev=1.0 -> cushion=1.0
    assert state.cushion_seconds() == pytest.approx(1.0, abs=1e-6)


def test_cushion_seconds_capped_at_max():
    cfg = CushionConfig(base_seconds=0.0, variance_factor=100.0, max_seconds=2.0)
    state = CushionState(config=cfg)
    for d in [0.0, 10.0]:
        state.record(make_result("cmd", d))
    assert state.cushion_seconds() == pytest.approx(2.0)


def test_state_window_trims_old_entries():
    cfg = CushionConfig(window=3)
    state = CushionState(config=cfg)
    for d in [1.0, 2.0, 3.0, 4.0, 5.0]:
        state.record(make_result("cmd", d))
    assert state._recent == [3.0, 4.0, 5.0]


# --- run_cushioned ---

def test_run_cushioned_returns_all_results():
    cmds = ["a", "b", "c"]
    results = run_cushioned(cmds, lambda c: make_result(c, 0.1), sleep_fn=lambda _: None)
    assert len(results) == 3
    assert [r.command for r in results] == cmds


def test_run_cushioned_no_sleep_for_first():
    slept: List[float] = []
    run_cushioned(["only"], lambda c: make_result(c, 0.5), sleep_fn=slept.append)
    assert slept == []


def test_run_cushioned_sleeps_between_commands():
    slept: List[float] = []
    cfg = CushionConfig(base_seconds=0.5)
    run_cushioned(["a", "b", "c"], lambda c: make_result(c, 0.1), config=cfg, sleep_fn=slept.append)
    assert len(slept) == 2
    assert all(s == pytest.approx(0.5) for s in slept)


def test_run_cushioned_disabled_no_sleep():
    slept: List[float] = []
    cfg = CushionConfig(base_seconds=1.0, enabled=False)
    run_cushioned(["a", "b"], lambda c: make_result(c, 0.1), config=cfg, sleep_fn=slept.append)
    assert slept == []
