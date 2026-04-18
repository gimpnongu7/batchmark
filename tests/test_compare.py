import pytest
from batchmark.runner import CommandResult
from batchmark.compare import compare_runs, format_compare_table, CompareEntry


def make_result(cmd, duration, status="success", returncode=0):
    return CommandResult(
        command=cmd,
        duration=duration,
        returncode=returncode,
        stdout="",
        stderr="",
        status=status,
    )


@pytest.fixture
def run_a():
    return [
        make_result("echo hello", 0.1),
        make_result("sleep 1", 1.0),
        make_result("ls /tmp", 0.05),
    ]


@pytest.fixture
def run_b():
    return [
        make_result("echo hello", 0.08),
        make_result("sleep 1", 1.2),
    ]


def test_compare_returns_all_commands(run_a, run_b):
    entries = compare_runs(run_a, run_b)
    commands = [e.command for e in entries]
    assert "echo hello" in commands
    assert "sleep 1" in commands
    assert "ls /tmp" in commands


def test_compare_delta_calculation(run_a, run_b):
    entries = compare_runs(run_a, run_b)
    entry = next(e for e in entries if e.command == "echo hello")
    assert abs(entry.delta - (0.08 - 0.1)) < 1e-9


def test_compare_pct_change(run_a, run_b):
    entries = compare_runs(run_a, run_b)
    entry = next(e for e in entries if e.command == "sleep 1")
    expected_pct = (1.2 - 1.0) / 1.0 * 100
    assert abs(entry.pct_change - expected_pct) < 1e-6


def test_compare_missing_in_b(run_a, run_b):
    entries = compare_runs(run_a, run_b)
    entry = next(e for e in entries if e.command == "ls /tmp")
    assert entry.duration_b is None
    assert entry.delta is None
    assert entry.pct_change is None


def test_format_compare_table_contains_header(run_a, run_b):
    entries = compare_runs(run_a, run_b)
    table = format_compare_table(entries)
    assert "Command" in table
    assert "Run A" in table
    assert "Delta" in table


def test_format_compare_table_contains_commands(run_a, run_b):
    entries = compare_runs(run_a, run_b)
    table = format_compare_table(entries)
    assert "echo hello" in table
    assert "sleep 1" in table
