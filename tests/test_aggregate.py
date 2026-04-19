import pytest
from batchmark.runner import CommandResult
from batchmark.aggregate import (
    aggregate_runs,
    format_aggregate_table,
    aggregate_to_dicts,
)


def make_result(command, status="success", duration=1.0):
    return CommandResult(
        command=command,
        returncode=0 if status == "success" else 1,
        stdout="",
        stderr="",
        duration=duration,
        status=status,
    )


@pytest.fixture
def two_runs():
    run_a = [
        make_result("echo hi", duration=0.5),
        make_result("sleep 1", duration=1.0),
    ]
    run_b = [
        make_result("echo hi", duration=0.7),
        make_result("sleep 1", duration=1.2, status="failure"),
    ]
    return [run_a, run_b]


def test_aggregate_groups_by_command(two_runs):
    entries = aggregate_runs(two_runs)
    commands = {e.command for e in entries}
    assert commands == {"echo hi", "sleep 1"}


def test_aggregate_run_count(two_runs):
    entries = aggregate_runs(two_runs)
    by_cmd = {e.command: e for e in entries}
    assert by_cmd["echo hi"].runs == 2
    assert by_cmd["sleep 1"].runs == 2


def test_aggregate_stats_mean(two_runs):
    entries = aggregate_runs(two_runs)
    by_cmd = {e.command: e for e in entries}
    assert abs(by_cmd["echo hi"].stats.mean - 0.6) < 1e-9


def test_aggregate_statuses(two_runs):
    entries = aggregate_runs(two_runs)
    by_cmd = {e.command: e for e in entries}
    assert by_cmd["sleep 1"].statuses.get("failure", 0) == 1
    assert by_cmd["sleep 1"].statuses.get("success", 0) == 1


def test_format_aggregate_table_contains_command(two_runs):
    entries = aggregate_runs(two_runs)
    table = format_aggregate_table(entries)
    assert "echo hi" in table
    assert "sleep 1" in table


def test_format_aggregate_table_header(two_runs):
    entries = aggregate_runs(two_runs)
    table = format_aggregate_table(entries)
    assert "Runs" in table
    assert "Mean" in table


def test_aggregate_to_dicts_keys(two_runs):
    entries = aggregate_runs(two_runs)
    dicts = aggregate_to_dicts(entries)
    assert len(dicts) == 2
    for d in dicts:
        assert "command" in d
        assert "mean" in d
        assert "runs" in d
        assert "statuses" in d


def test_aggregate_single_run():
    run = [make_result("ls", duration=0.1)]
    entries = aggregate_runs([run])
    assert entries[0].runs == 1
    assert entries[0].stats.mean == pytest.approx(0.1)
