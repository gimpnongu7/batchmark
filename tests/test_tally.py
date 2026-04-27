import pytest
from batchmark.runner import CommandResult
from batchmark.tally import (
    TallyConfig,
    TallyEntry,
    parse_tally_config,
    tally_results,
    tally_summary,
)


def make_result(command: str, status: str, duration: float = 0.5) -> CommandResult:
    return CommandResult(
        command=command,
        status=status,
        returncode=0 if status == "success" else 1,
        duration=duration,
        stdout="",
        stderr="",
    )


@pytest.fixture
def sample_results():
    return [
        make_result("echo a", "success"),
        make_result("echo a", "success"),
        make_result("echo a", "failure"),
        make_result("sleep 1", "timeout"),
        make_result("sleep 1", "success"),
        make_result("ls", "failure"),
    ]


def test_parse_tally_config_defaults():
    cfg = parse_tally_config({})
    assert cfg.group_by == "command"
    assert cfg.min_runs == 1


def test_parse_tally_config_custom():
    cfg = parse_tally_config({"group_by": "status", "min_runs": 2})
    assert cfg.group_by == "status"
    assert cfg.min_runs == 2


def test_tally_returns_one_entry_per_command(sample_results):
    entries = tally_results(sample_results)
    commands = {e.command for e in entries}
    assert commands == {"echo a", "sleep 1", "ls"}


def test_tally_counts_correct(sample_results):
    entries = tally_results(sample_results)
    echo = next(e for e in entries if e.command == "echo a")
    assert echo.total == 3
    assert echo.successes == 2
    assert echo.failures == 1
    assert echo.timeouts == 0


def test_tally_timeout_counted(sample_results):
    entries = tally_results(sample_results)
    sleep = next(e for e in entries if e.command == "sleep 1")
    assert sleep.timeouts == 1
    assert sleep.successes == 1


def test_tally_success_rate(sample_results):
    entries = tally_results(sample_results)
    echo = next(e for e in entries if e.command == "echo a")
    assert echo.success_rate == pytest.approx(2 / 3, rel=1e-3)


def test_tally_failure_rate_includes_timeout(sample_results):
    entries = tally_results(sample_results)
    sleep = next(e for e in entries if e.command == "sleep 1")
    # 1 timeout out of 2 runs
    assert sleep.failure_rate == pytest.approx(0.5, rel=1e-3)


def test_tally_min_runs_filters(sample_results):
    cfg = TallyConfig(min_runs=2)
    entries = tally_results(sample_results, config=cfg)
    commands = {e.command for e in entries}
    # "ls" has only 1 run, should be excluded
    assert "ls" not in commands
    assert "echo a" in commands


def test_tally_group_by_status(sample_results):
    cfg = TallyConfig(group_by="status")
    entries = tally_results(sample_results, config=cfg)
    keys = {e.command for e in entries}
    assert "success" in keys
    assert "failure" in keys
    assert "timeout" in keys


def test_tally_summary_keys(sample_results):
    entries = tally_results(sample_results)
    summary = tally_summary(entries)
    assert "groups" in summary
    assert "total_runs" in summary
    assert "total_successes" in summary
    assert "total_failures" in summary
    assert "total_timeouts" in summary


def test_tally_summary_values(sample_results):
    entries = tally_results(sample_results)
    summary = tally_summary(entries)
    assert summary["total_runs"] == 6
    assert summary["total_successes"] == 3
    assert summary["total_timeouts"] == 1
    assert summary["groups"] == 3
