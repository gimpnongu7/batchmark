"""Tests for batchmark.cooldown."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import pytest

from batchmark.cooldown import (
    CooldownConfig,
    CooldownState,
    _cooldown_seconds,
    parse_cooldown_config,
    run_with_cooldown,
)
from batchmark.runner import CommandResult


def make_result(cmd: str = "echo hi", status: str = "success", duration: float = 0.1) -> CommandResult:
    return CommandResult(command=cmd, stdout="", stderr="", returncode=0, duration=duration, status=status)


# --- _cooldown_seconds ---

def test_cooldown_seconds_none_result():
    cfg = CooldownConfig(seconds=1.0)
    assert _cooldown_seconds(cfg, None) == 0.0


def test_cooldown_seconds_success():
    cfg = CooldownConfig(seconds=0.5, after_failure=2.0)
    assert _cooldown_seconds(cfg, make_result(status="success")) == 0.5


def test_cooldown_seconds_failure_adds_extra():
    cfg = CooldownConfig(seconds=0.5, after_failure=1.5)
    assert _cooldown_seconds(cfg, make_result(status="failure")) == 2.0


def test_cooldown_seconds_timeout_adds_extra():
    cfg = CooldownConfig(seconds=0.5, after_timeout=3.0)
    assert _cooldown_seconds(cfg, make_result(status="timeout")) == 3.5


# --- parse_cooldown_config ---

def test_parse_cooldown_config_defaults():
    cfg = parse_cooldown_config({})
    assert cfg.seconds == 0.0
    assert cfg.after_failure == 0.0
    assert cfg.after_timeout == 0.0


def test_parse_cooldown_config_full():
    raw = {"cooldown": {"seconds": 1.0, "after_failure": 2.0, "after_timeout": 5.0}}
    cfg = parse_cooldown_config(raw)
    assert cfg.seconds == 1.0
    assert cfg.after_failure == 2.0
    assert cfg.after_timeout == 5.0


# --- run_with_cooldown ---

def test_run_with_cooldown_no_delay_before_first():
    sleeps: List[float] = []
    commands = ["echo a", "echo b"]
    results_map = {cmd: make_result(cmd) for cmd in commands}

    results, state = run_with_cooldown(
        commands,
        CooldownConfig(seconds=0.2),
        lambda cmd: results_map[cmd],
        sleep_fn=sleeps.append,
    )
    # first command must not sleep; second must
    assert len(sleeps) == 1
    assert sleeps[0] == pytest.approx(0.2)


def test_run_with_cooldown_returns_all_results():
    commands = ["a", "b", "c"]
    results, state = run_with_cooldown(
        commands,
        CooldownConfig(seconds=0.0),
        lambda cmd: make_result(cmd),
        sleep_fn=lambda _: None,
    )
    assert len(results) == 3
    assert [r.command for r in results] == commands


def test_run_with_cooldown_extra_pause_after_failure():
    sleeps: List[float] = []
    commands = ["fail", "ok"]
    statuses = {"fail": "failure", "ok": "success"}

    run_with_cooldown(
        commands,
        CooldownConfig(seconds=0.1, after_failure=0.9),
        lambda cmd: make_result(cmd, status=statuses[cmd]),
        sleep_fn=sleeps.append,
    )
    assert sleeps[0] == pytest.approx(1.0)


def test_cooldown_state_tracks_totals():
    sleeps: List[float] = []
    commands = ["a", "b", "c"]

    _, state = run_with_cooldown(
        commands,
        CooldownConfig(seconds=0.5),
        lambda cmd: make_result(cmd),
        sleep_fn=sleeps.append,
    )
    assert state.pause_count == 2
    assert state.paused_total == pytest.approx(1.0)


def test_no_sleep_when_seconds_zero():
    sleeps: List[float] = []
    run_with_cooldown(
        ["a", "b"],
        CooldownConfig(seconds=0.0),
        lambda cmd: make_result(cmd),
        sleep_fn=sleeps.append,
    )
    assert sleeps == []
