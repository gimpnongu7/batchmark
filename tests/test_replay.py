"""Tests for batchmark.replay."""
from __future__ import annotations

import pytest
from batchmark.runner import CommandResult
from batchmark.replay import (
    ReplayConfig,
    ReplayResult,
    _should_replay,
    replay_results,
    parse_replay_config,
)


def make_result(cmd="echo hi", status="success", duration=0.5, returncode=0):
    return CommandResult(command=cmd, status=status, duration=duration,
                         returncode=returncode, stdout="", stderr="")


def _fake_run(cmd: str) -> CommandResult:
    return make_result(cmd=cmd, status="success", duration=0.1)


def test_should_replay_failure():
    cfg = ReplayConfig(rerun_failed=True)
    assert _should_replay(make_result(status="failure"), cfg) is True


def test_should_not_replay_success():
    cfg = ReplayConfig(rerun_failed=True)
    assert _should_replay(make_result(status="success"), cfg) is False


def test_should_replay_timeout():
    cfg = ReplayConfig(rerun_timeout=True)
    assert _should_replay(make_result(status="timeout"), cfg) is True


def test_should_not_replay_timeout_when_disabled():
    cfg = ReplayConfig(rerun_timeout=False)
    assert _should_replay(make_result(status="timeout"), cfg) is False


def test_replay_results_replays_failures():
    results = [make_result(status="failure"), make_result(status="success")]
    cfg = ReplayConfig()
    out = replay_results(results, cfg, _fake_run)
    assert out[0].was_replayed is True
    assert out[1].was_replayed is False


def test_replay_results_final_is_replayed():
    results = [make_result(status="failure", duration=2.0)]
    cfg = ReplayConfig()
    out = replay_results(results, cfg, _fake_run)
    assert out[0].final.status == "success"
    assert out[0].final.duration == 0.1


def test_replay_results_respects_max_replays():
    results = [make_result(status="failure")] * 5
    cfg = ReplayConfig(max_replays=2)
    out = replay_results(results, cfg, _fake_run)
    replayed = [r for r in out if r.was_replayed]
    assert len(replayed) == 2


def test_replay_result_final_returns_original_when_not_replayed():
    r = make_result(status="success", duration=1.0)
    rr = ReplayResult(original=r)
    assert rr.final is r


def test_parse_replay_config_defaults():
    cfg = parse_replay_config({})
    assert cfg.rerun_failed is True
    assert cfg.rerun_timeout is True
    assert cfg.max_replays is None


def test_parse_replay_config_full():
    cfg = parse_replay_config({"replay": {"rerun_failed": False, "rerun_timeout": False, "max_replays": 3}})
    assert cfg.rerun_failed is False
    assert cfg.rerun_timeout is False
    assert cfg.max_replays == 3
