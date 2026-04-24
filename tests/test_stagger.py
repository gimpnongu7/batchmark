"""Tests for batchmark.stagger and batchmark.stagger_report."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List

import pytest

from batchmark.runner import CommandResult
from batchmark.stagger import (
    StaggerConfig,
    StaggerState,
    parse_stagger_config,
    run_staggered,
)
from batchmark.stagger_report import (
    format_stagger_json,
    format_stagger_table,
    stagger_summary,
)


def make_result(cmd: str, status: str = "success", duration: float = 0.5) -> CommandResult:
    return CommandResult(command=cmd, status=status, duration=duration, stdout="", stderr="")


# ---------------------------------------------------------------------------
# StaggerConfig / parse
# ---------------------------------------------------------------------------

def test_parse_stagger_config_defaults():
    cfg = parse_stagger_config({})
    assert cfg.delay == 0.0
    assert cfg.step == 0.0
    assert cfg.max_delay is None
    assert cfg.jitter == 0.0


def test_parse_stagger_config_full():
    cfg = parse_stagger_config({"delay": 1.0, "step": 0.2, "max_delay": 3.0, "jitter": 0.1})
    assert cfg.delay == 1.0
    assert cfg.step == 0.2
    assert cfg.max_delay == 3.0
    assert cfg.jitter == 0.1


# ---------------------------------------------------------------------------
# StaggerState.next_delay
# ---------------------------------------------------------------------------

def test_next_delay_base_only():
    state = StaggerState(config=StaggerConfig(delay=0.5))
    assert state.next_delay() == pytest.approx(0.5)
    assert state.next_delay() == pytest.approx(0.5)


def test_next_delay_with_step():
    state = StaggerState(config=StaggerConfig(delay=0.1, step=0.2))
    assert state.next_delay() == pytest.approx(0.1)   # index 0
    assert state.next_delay() == pytest.approx(0.3)   # index 1
    assert state.next_delay() == pytest.approx(0.5)   # index 2


def test_next_delay_capped_by_max():
    state = StaggerState(config=StaggerConfig(delay=1.0, step=1.0, max_delay=2.0))
    assert state.next_delay() == pytest.approx(1.0)
    assert state.next_delay() == pytest.approx(2.0)
    assert state.next_delay() == pytest.approx(2.0)  # capped


def test_next_delay_jitter_applied():
    # rng always returns 1.0 -> jitter factor = 1 + jitter*(2-1) = 1 + jitter
    state = StaggerState(config=StaggerConfig(delay=1.0, jitter=0.5))
    delay = state.next_delay(rng=lambda: 1.0)
    assert delay == pytest.approx(1.5)


# ---------------------------------------------------------------------------
# run_staggered
# ---------------------------------------------------------------------------

def test_run_staggered_returns_all_results():
    cmds = ["echo a", "echo b", "echo c"]
    results = run_staggered(
        cmds,
        run_fn=lambda c: make_result(c),
        config=StaggerConfig(delay=0.0),
        sleep_fn=lambda _: None,
    )
    assert len(results) == 3
    assert [r.command for r in results] == cmds


def test_run_staggered_calls_sleep_correct_times():
    sleeps: List[float] = []
    run_staggered(
        ["a", "b", "c"],
        run_fn=lambda c: make_result(c),
        config=StaggerConfig(delay=0.3),
        sleep_fn=sleeps.append,
    )
    # first command: delay=0.3, second: 0.3, third: 0.3
    assert len(sleeps) == 3
    assert all(s == pytest.approx(0.3) for s in sleeps)


def test_run_staggered_no_sleep_when_zero_delay():
    sleeps: List[float] = []
    run_staggered(
        ["x", "y"],
        run_fn=lambda c: make_result(c),
        config=StaggerConfig(delay=0.0),
        sleep_fn=sleeps.append,
    )
    assert sleeps == []


# ---------------------------------------------------------------------------
# stagger_report
# ---------------------------------------------------------------------------

def test_stagger_summary_counts():
    results = [make_result("a"), make_result("b")]
    s = stagger_summary(results, total_stagger_time=1.5)
    assert s["command_count"] == 2
    assert s["total_stagger_time_s"] == pytest.approx(1.5)
    assert s["mean_stagger_time_s"] == pytest.approx(0.75)


def test_format_stagger_json_valid():
    results = [make_result("echo hi")]
    delays = [0.2]
    out = format_stagger_json(results, delays, total_stagger_time=0.2)
    data = json.loads(out)
    assert "summary" in data
    assert "results" in data
    assert data["results"][0]["command"] == "echo hi"
    assert data["results"][0]["stagger_delay"] == pytest.approx(0.2)


def test_format_stagger_table_header():
    results = [make_result("ls")]
    table = format_stagger_table(results, [0.1])
    assert "command" in table
    assert "delay" in table
    assert "ls" in table
