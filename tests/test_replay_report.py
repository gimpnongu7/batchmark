"""Tests for batchmark.replay_report."""
from __future__ import annotations

import json
import pytest
from batchmark.runner import CommandResult
from batchmark.replay import ReplayResult
from batchmark.replay_report import (
    replay_result_to_dict,
    format_replay_json,
    format_replay_table,
)


def make_result(cmd="echo hi", status="success", duration=0.5):
    return CommandResult(command=cmd, status=status, duration=duration,
                         returncode=0, stdout="", stderr="")


def make_rr(replayed=False):
    orig = make_result(status="failure", duration=2.0)
    if replayed:
        rep = make_result(status="success", duration=0.3)
        return ReplayResult(original=orig, replayed=rep, was_replayed=True)
    return ReplayResult(original=orig)


def test_replay_result_to_dict_keys():
    d = replay_result_to_dict(make_rr())
    assert set(d.keys()) == {"command", "was_replayed", "original_status",
                              "original_duration", "final_status", "final_duration", "delta"}


def test_replay_result_to_dict_not_replayed():
    d = replay_result_to_dict(make_rr(replayed=False))
    assert d["was_replayed"] is False
    assert d["delta"] is None
    assert d["final_status"] == "failure"


def test_replay_result_to_dict_replayed():
    d = replay_result_to_dict(make_rr(replayed=True))
    assert d["was_replayed"] is True
    assert d["final_status"] == "success"
    assert d["delta"] == pytest.approx(0.3 - 2.0, abs=1e-4)


def test_format_replay_json_valid():
    rrs = [make_rr(True), make_rr(False)]
    out = format_replay_json(rrs)
    parsed = json.loads(out)
    assert len(parsed) == 2
    assert "was_replayed" in parsed[0]


def test_format_replay_table_header():
    out = format_replay_table([make_rr()])
    assert "Command" in out
    assert "Replayed" in out
    assert "Delta" in out


def test_format_replay_table_row_count():
    rrs = [make_rr(True), make_rr(False), make_rr(True)]
    lines = [l for l in format_replay_table(rrs).splitlines() if l.strip() and not l.startswith("-")]
    # header + 3 data rows
    assert len(lines) == 4
