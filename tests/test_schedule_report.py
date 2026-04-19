import json
import pytest
from batchmark.schedule import ScheduleEntry, ScheduleResult
from batchmark.runner import CommandResult
from batchmark.schedule_report import (
    schedule_results_to_dicts, format_schedule_json, format_schedule_table
)


def make_sr(cmd="echo hi", status="success", duration=0.25, delay=0.1, tags=None):
    entry = ScheduleEntry(command=cmd, delay=delay, tags=tags or [])
    result = CommandResult(command=cmd, status=status, returncode=0,
                          stdout="hi", stderr="", duration=duration)
    return ScheduleResult(entry=entry, result=result, scheduled_at=1.0, started_at=1.1)


def test_results_to_dicts_keys():
    dicts = schedule_results_to_dicts([make_sr()])
    assert len(dicts) == 1
    d = dicts[0]
    assert "command" in d
    assert "status" in d
    assert "duration" in d
    assert "wait_time" in d
    assert "tags" in d


def test_results_to_dicts_values():
    sr = make_sr(cmd="ls", status="success", duration=0.5, delay=0.2, tags=["t1"])
    d = schedule_results_to_dicts([sr])[0]
    assert d["command"] == "ls"
    assert d["duration"] == 0.5
    assert d["tags"] == ["t1"]
    assert abs(d["wait_time"] - 0.1) < 0.01


def test_format_schedule_json_valid():
    out = format_schedule_json([make_sr()])
    parsed = json.loads(out)
    assert "schedule_results" in parsed
    assert len(parsed["schedule_results"]) == 1


def test_format_schedule_table_header():
    out = format_schedule_table([make_sr()])
    assert "COMMAND" in out
    assert "STATUS" in out
    assert "DURATION" in out


def test_format_schedule_table_row():
    out = format_schedule_table([make_sr(cmd="echo hi", tags=["greet"])])
    assert "echo hi" in out
    assert "greet" in out
    assert "success" in out
