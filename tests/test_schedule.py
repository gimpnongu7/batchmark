import pytest
from unittest.mock import patch, MagicMock
from batchmark.schedule import (
    ScheduleEntry, ScheduleConfig, ScheduleResult,
    parse_schedule_config, run_schedule,
)
from batchmark.runner import CommandResult


def make_result(cmd="echo hi", status="success", duration=0.1):
    return CommandResult(command=cmd, status=status, returncode=0,
                        stdout="hi", stderr="", duration=duration)


def _fake_run_batch(commands, timeout=None):
    return [make_result(cmd=c) for c in commands]


def test_parse_schedule_config_basic():
    raw = {
        "global_delay": 0.2,
        "max_concurrency": 2,
        "entries": [
            {"command": "echo a", "delay": 0.1, "tags": ["x"]},
            {"command": "echo b"},
        ],
    }
    cfg = parse_schedule_config(raw)
    assert cfg.global_delay == 0.2
    assert cfg.max_concurrency == 2
    assert len(cfg.entries) == 2
    assert cfg.entries[0].command == "echo a"
    assert cfg.entries[0].delay == 0.1
    assert cfg.entries[0].tags == ["x"]
    assert cfg.entries[1].delay == 0.0


def test_parse_schedule_config_defaults():
    cfg = parse_schedule_config({"entries": [{"command": "ls"}]})
    assert cfg.global_delay == 0.0
    assert cfg.max_concurrency == 1


def test_run_schedule_returns_all(monkeypatch):
    monkeypatch.setattr("batchmark.schedule.run_batch", _fake_run_batch)
    monkeypatch.setattr("batchmark.schedule.time.sleep", lambda _: None)
    cfg = ScheduleConfig(entries=[
        ScheduleEntry(command="echo a"),
        ScheduleEntry(command="echo b"),
    ])
    results = run_schedule(cfg)
    assert len(results) == 2
    assert results[0].entry.command == "echo a"
    assert results[1].entry.command == "echo b"


def test_run_schedule_calls_on_result(monkeypatch):
    monkeypatch.setattr("batchmark.schedule.run_batch", _fake_run_batch)
    monkeypatch.setattr("batchmark.schedule.time.sleep", lambda _: None)
    cfg = ScheduleConfig(entries=[ScheduleEntry(command="echo x")])
    seen = []
    run_schedule(cfg, on_result=seen.append)
    assert len(seen) == 1
    assert seen[0].entry.command == "echo x"


def test_schedule_result_wait_time():
    entry = ScheduleEntry(command="echo")
    result = make_result()
    sr = ScheduleResult(entry=entry, result=result, scheduled_at=1.0, started_at=1.3)
    assert abs(sr.wait_time - 0.3) < 1e-9


def test_run_schedule_sleeps_global_delay(monkeypatch):
    monkeypatch.setattr("batchmark.schedule.run_batch", _fake_run_batch)
    sleep_calls = []
    monkeypatch.setattr("batchmark.schedule.time.sleep", lambda s: sleep_calls.append(s))
    cfg = ScheduleConfig(
        entries=[ScheduleEntry(command="a"), ScheduleEntry(command="b")],
        global_delay=0.5,
    )
    run_schedule(cfg)
    assert 0.5 in sleep_calls
