"""Integration tests: throttle wired into a fake batch run."""
from __future__ import annotations
from typing import List
from batchmark.runner import CommandResult
from batchmark.throttle import ThrottleConfig, parse_throttle_config, run_throttled


def make_result(cmd: str) -> CommandResult:
    return CommandResult(command=cmd, status="success", duration=0.05, stdout="ok", stderr="", returncode=0)


def _fake_run_batch(commands: List[str], cfg: ThrottleConfig) -> List[CommandResult]:
    delays: List[float] = []
    results = run_throttled(commands, cfg, make_result, sleep_fn=delays.append)
    return results, delays


def test_full_run_no_throttle():
    cmds = ["echo 1", "echo 2", "echo 3"]
    results, delays = _fake_run_batch(cmds, ThrottleConfig())
    assert len(results) == 3
    assert delays == []


def test_full_run_with_delay():
    cmds = ["a", "b", "c", "d"]
    cfg = ThrottleConfig(inter_command_delay=0.25)
    results, delays = _fake_run_batch(cmds, cfg)
    assert len(results) == 4
    assert len(delays) == 3
    assert all(d == 0.25 for d in delays)


def test_full_run_burst_reduces_delays():
    cmds = ["a", "b", "c", "d", "e", "f"]
    cfg = ThrottleConfig(inter_command_delay=0.1, burst=3)
    results, delays = _fake_run_batch(cmds, cfg)
    # delays at index 3 only (6 commands, burst=3 → index 3)
    assert len(delays) == 1


def test_parse_and_run_roundtrip():
    raw = {"inter_command_delay": 0.05, "burst": 2}
    cfg = parse_throttle_config(raw)
    cmds = ["x", "y", "z", "w"]
    results, delays = _fake_run_batch(cmds, cfg)
    assert [r.status for r in results] == ["success"] * 4
    # burst=2: delay at index 2 only for 4 commands
    assert len(delays) == 1


def test_single_command_no_delay():
    cfg = ThrottleConfig(inter_command_delay=1.0)
    results, delays = _fake_run_batch(["solo"], cfg)
    assert len(results) == 1
    assert delays == []
