import pytest
from batchmark.quota import QuotaConfig, QuotaState, parse_quota_config, run_with_quota
from batchmark.quota_report import quota_state_to_dict, format_quota_json, format_quota_table
from batchmark.runner import CommandResult


def make_result(cmd="echo hi", status="success", duration=0.1):
    return CommandResult(command=cmd, status=status, duration=duration, stdout="", stderr="", returncode=0)


def test_parse_quota_config_defaults():
    cfg = parse_quota_config({})
    assert cfg.max_failures is None
    assert cfg.max_duration is None
    assert cfg.max_commands is None


def test_parse_quota_config_full():
    cfg = parse_quota_config({"max_failures": 2, "max_duration": 10.0, "max_commands": 5})
    assert cfg.max_failures == 2
    assert cfg.max_duration == 10.0
    assert cfg.max_commands == 5


def test_quota_state_no_exceeded():
    state = QuotaState(config=QuotaConfig(max_failures=3))
    state.record(make_result(status="success"))
    assert state.exceeded() is None


def test_quota_state_failure_exceeded():
    state = QuotaState(config=QuotaConfig(max_failures=2))
    state.record(make_result(status="failure"))
    state.record(make_result(status="failure"))
    reason = state.exceeded()
    assert reason is not None
    assert "failure quota" in reason


def test_quota_state_duration_exceeded():
    state = QuotaState(config=QuotaConfig(max_duration=0.5))
    state.record(make_result(duration=0.6))
    assert state.exceeded() is not None


def test_quota_state_commands_exceeded():
    state = QuotaState(config=QuotaConfig(max_commands=1))
    state.record(make_result())
    assert "command quota" in state.exceeded()


def test_run_with_quota_stops_early():
    cmds = ["a", "b", "c", "d"]
    cfg = QuotaConfig(max_commands=2)
    results, state = run_with_quota(cmds, cfg, lambda c: make_result(cmd=c))
    assert len(results) == 2
    assert state.stopped_reason is not None


def test_run_with_quota_all_pass():
    cmds = ["a", "b"]
    cfg = QuotaConfig(max_failures=5)
    results, state = run_with_quota(cmds, cfg, lambda c: make_result(cmd=c))
    assert len(results) == 2
    assert state.stopped_reason is None


def test_quota_state_to_dict_keys():
    state = QuotaState(config=QuotaConfig(max_failures=1), failures=1, commands_run=1, stopped_reason="x")
    d = quota_state_to_dict(state)
    assert "commands_run" in d and "failures" in d and "stopped_reason" in d


def test_format_quota_json_valid():
    results = [make_result()]
    state = QuotaState(config=QuotaConfig(), commands_run=1)
    import json
    obj = json.loads(format_quota_json(results, state))
    assert "results" in obj and "quota_summary" in obj


def test_format_quota_table_includes_stopped():
    results = [make_result()]
    state = QuotaState(config=QuotaConfig(), commands_run=1, stopped_reason="failure quota reached (1/1)")
    out = format_quota_table(results, state)
    assert "Stopped" in out
