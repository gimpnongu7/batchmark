import pytest
from unittest.mock import patch
from batchmark.repeat import RepeatConfig, RepeatSummary, repeat_batch, summaries_to_dict
from batchmark.runner import CommandResult


def make_result(cmd, status="success", duration=1.0):
    return CommandResult(command=cmd, status=status, duration=duration, stdout="", stderr="", returncode=0)


@pytest.fixture
def two_commands():
    return ["echo hello", "echo world"]


def _fake_run_batch(commands, timeout=None):
    return [make_result(c) for c in commands]


def test_repeat_returns_one_summary_per_command(two_commands):
    with patch("batchmark.repeat.run_batch", side_effect=_fake_run_batch):
        summaries = repeat_batch(two_commands, RepeatConfig(times=2))
    assert len(summaries) == 2
    assert {s.command for s in summaries} == set(two_commands)


def test_repeat_correct_run_count(two_commands):
    with patch("batchmark.repeat.run_batch", side_effect=_fake_run_batch):
        summaries = repeat_batch(two_commands, RepeatConfig(times=4))
    for s in summaries:
        assert len(s.runs) == 4


def test_repeat_success_count():
    s = RepeatSummary(command="echo hi")
    s.runs = [make_result("echo hi", "success"), make_result("echo hi", "failure"), make_result("echo hi", "success")]
    assert s.success_count == 2
    assert s.failure_count == 1


def test_repeat_mean_duration():
    s = RepeatSummary(command="cmd")
    s.runs = [make_result("cmd", duration=1.0), make_result("cmd", duration=3.0)]
    assert s.mean_duration == 2.0


def test_repeat_min_max_duration():
    s = RepeatSummary(command="cmd")
    s.runs = [make_result("cmd", duration=0.5), make_result("cmd", duration=2.5), make_result("cmd", duration=1.0)]
    assert s.min_duration == 0.5
    assert s.max_duration == 2.5


def test_stop_on_error_halts_early():
    call_count = 0

    def failing_batch(commands, timeout=None):
        nonlocal call_count
        call_count += 1
        return [make_result(c, status="failure") for c in commands]

    with patch("batchmark.repeat.run_batch", side_effect=failing_batch):
        repeat_batch(["cmd"], RepeatConfig(times=5, stop_on_error=True))
    assert call_count == 1


def test_on_run_callback_called():
    calls = []
    with patch("batchmark.repeat.run_batch", side_effect=_fake_run_batch):
        repeat_batch(["echo"], RepeatConfig(times=3), on_run=lambda i, r: calls.append(i))
    assert calls == [1, 2, 3]


def test_summaries_to_dict():
    s = RepeatSummary(command="ls")
    s.runs = [make_result("ls", duration=0.1), make_result("ls", duration=0.3)]
    result = summaries_to_dict([s])
    assert len(result) == 1
    d = result[0]
    assert d["command"] == "ls"
    assert d["runs"] == 2
    assert d["mean_duration"] == 0.2
    assert d["min_duration"] == 0.1
    assert d["max_duration"] == 0.3
