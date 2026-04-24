"""Tests for batchmark.cushion_report."""
from __future__ import annotations

import json

import pytest

from batchmark.cushion import CushionConfig, CushionState
from batchmark.cushion_report import (
    format_cushion_json,
    format_cushion_table,
    state_to_dict,
)
from batchmark.runner import CommandResult


def make_result(cmd: str, duration: float) -> CommandResult:
    return CommandResult(command=cmd, duration=duration, status="success", stdout="", stderr="", returncode=0)


@pytest.fixture()
def state() -> CushionState:
    cfg = CushionConfig(base_seconds=0.3, variance_factor=0.2, window=4, max_seconds=5.0)
    s = CushionState(config=cfg)
    for d in [0.5, 1.5, 0.5, 1.5]:
        s.record(make_result("echo hi", d))
    s.total_paused = 1.2
    s.pause_count = 4
    return s


def test_state_to_dict_keys(state):
    d = state_to_dict(state)
    expected = {
        "enabled", "base_seconds", "variance_factor", "window",
        "max_seconds", "total_paused", "pause_count", "current_cushion",
    }
    assert set(d.keys()) == expected


def test_state_to_dict_values(state):
    d = state_to_dict(state)
    assert d["base_seconds"] == pytest.approx(0.3)
    assert d["pause_count"] == 4
    assert d["total_paused"] == pytest.approx(1.2)
    assert d["enabled"] is True


def test_format_cushion_json_valid(state):
    output = format_cushion_json(state)
    parsed = json.loads(output)
    assert "current_cushion" in parsed
    assert "total_paused" in parsed


def test_format_cushion_table_header(state):
    output = format_cushion_table(state)
    assert "Cushion Summary" in output


def test_format_cushion_table_has_pause_count(state):
    output = format_cushion_table(state)
    assert "4" in output


def test_format_cushion_table_shows_base_seconds(state):
    output = format_cushion_table(state)
    assert "0.300" in output
