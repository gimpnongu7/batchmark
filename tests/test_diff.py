import pytest
from batchmark.runner import CommandResult
from batchmark.diff import DiffEntry, diff_runs, format_diff_table


def make_result(cmd, status="success", duration=1.0):
    return CommandResult(command=cmd, status=status, duration=duration, stdout="", stderr="", returncode=0)


@pytest.fixture
def run_a():
    return [
        make_result("echo hello", duration=0.5),
        make_result("sleep 1", duration=1.0),
        make_result("ls /tmp", status="success", duration=0.2),
    ]


@pytest.fixture
def run_b():
    return [
        make_result("echo hello", duration=0.4),
        make_result("sleep 1", status="failure", duration=1.5),
        make_result("cat /etc/hosts", duration=0.1),
    ]


def test_diff_returns_all_commands(run_a, run_b):
    entries = diff_runs(run_a, run_b)
    commands = {e.command for e in entries}
    assert "echo hello" in commands
    assert "sleep 1" in commands
    assert "ls /tmp" in commands
    assert "cat /etc/hosts" in commands


def test_diff_delta_calculation(run_a, run_b):
    entries = diff_runs(run_a, run_b)
    e = next(e for e in entries if e.command == "echo hello")
    assert abs(e.duration_delta - (-0.1)) < 1e-9


def test_diff_status_changed(run_a, run_b):
    entries = diff_runs(run_a, run_b)
    e = next(e for e in entries if e.command == "sleep 1")
    assert e.status_changed is True


def test_diff_status_unchanged(run_a, run_b):
    entries = diff_runs(run_a, run_b)
    e = next(e for e in entries if e.command == "echo hello")
    assert e.status_changed is False


def test_diff_missing_in_b(run_a, run_b):
    entries = diff_runs(run_a, run_b)
    e = next(e for e in entries if e.command == "ls /tmp")
    assert e.status_b is None
    assert e.duration_b is None
    assert e.duration_delta is None


def test_diff_missing_in_a(run_a, run_b):
    entries = diff_runs(run_a, run_b)
    e = next(e for e in entries if e.command == "cat /etc/hosts")
    assert e.status_a is None
    assert e.duration_pct is None


def test_format_diff_table_contains_header(run_a, run_b):
    entries = diff_runs(run_a, run_b)
    table = format_diff_table(entries)
    assert "Command" in table
    assert "Delta" in table


def test_format_diff_table_marks_status_change(run_a, run_b):
    entries = diff_runs(run_a, run_b)
    table = format_diff_table(entries)
    lines = table.splitlines()
    sleep_line = next(l for l in lines if "sleep 1" in l)
    assert "*" in sleep_line
