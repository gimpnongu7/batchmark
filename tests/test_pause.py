import pytest
from unittest.mock import patch, call
from batchmark.runner import CommandResult
from batchmark.pause import (
    PauseConfig, PauseState, parse_pause_config,
    _should_pause, run_with_pauses,
)
from batchmark.pause_report import pause_state_to_dict, format_pause_json, format_pause_table


def make_result(cmd="echo hi", status="success", duration=0.1):
    return CommandResult(command=cmd, status=status, duration=duration, stdout="", stderr="", returncode=0)


def test_parse_pause_config_defaults():
    cfg = parse_pause_config({})
    assert cfg.after_every == 0
    assert cfg.pause_seconds == 1.0
    assert cfg.after_commands == []


def test_parse_pause_config_full():
    cfg = parse_pause_config({"after_every": 3, "pause_seconds": 0.5, "after_commands": ["sleep 1"]})
    assert cfg.after_every == 3
    assert cfg.pause_seconds == 0.5
    assert cfg.after_commands == ["sleep 1"]


def test_should_pause_after_specific_command():
    cfg = PauseConfig(after_commands=["echo hi"])
    state = PauseState(count=1)
    r = make_result(cmd="echo hi")
    assert _should_pause(cfg, state, r) is True


def test_should_not_pause_unrelated_command():
    cfg = PauseConfig(after_commands=["echo hi"])
    state = PauseState(count=1)
    r = make_result(cmd="ls")
    assert _should_pause(cfg, state, r) is False


def test_should_pause_after_every():
    cfg = PauseConfig(after_every=2)
    state = PauseState(count=2)
    r = make_result(cmd="ls")
    assert _should_pause(cfg, state, r) is True


def test_should_not_pause_after_every_not_boundary():
    cfg = PauseConfig(after_every=2)
    state = PauseState(count=1)
    r = make_result(cmd="ls")
    assert _should_pause(cfg, state, r) is False


def test_run_with_pauses_no_pause():
    results = [make_result() for _ in range(3)]
    cfg = PauseConfig(after_every=0)
    slept = []
    out, state = run_with_pauses(results, cfg, _sleep=slept.append)
    assert len(out) == 3
    assert slept == []
    assert state.pause_count == 0


def test_run_with_pauses_after_every():
    results = [make_result(cmd=f"cmd{i}") for i in range(4)]
    cfg = PauseConfig(after_every=2, pause_seconds=0.5)
    slept = []
    out, state = run_with_pauses(results, cfg, _sleep=slept.append)
    assert len(out) == 4
    assert state.pause_count == 2
    assert state.total_paused == pytest.approx(1.0)


def test_pause_state_to_dict():
    state = PauseState(count=5, total_paused=2.0, pause_count=2)
    d = pause_state_to_dict(state)
    assert d["commands_run"] == 5
    assert d["pause_count"] == 2
    assert d["total_paused_seconds"] == 2.0


def test_format_pause_table_contains_header():
    state = PauseState(count=3, total_paused=1.5, pause_count=1)
    table = format_pause_table(state)
    assert "Pause Summary" in table
    assert "1.5" in table


def test_format_pause_json_valid():
    import json
    state = PauseState(count=2, total_paused=0.5, pause_count=1)
    parsed = json.loads(format_pause_json(state))
    assert parsed["pause_count"] == 1
