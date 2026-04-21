"""Tests for batchmark.correlate."""
import pytest
from batchmark.runner import CommandResult
from batchmark.correlate import CorrelateEntry, correlate_runs, format_correlate_table


def make_result(command: str, duration: float, status: str = "success") -> CommandResult:
    return CommandResult(command=command, duration=duration, status=status, stdout="", stderr="", returncode=0)


@pytest.fixture
def run_a():
    return [
        make_result("echo hello", 0.10),
        make_result("sleep 0.1", 0.20),
        make_result("ls /tmp", 0.05),
    ]


@pytest.fixture
def run_b():
    return [
        make_result("echo hello", 0.08),
        make_result("sleep 0.1", 0.25),
        make_result("date", 0.03),
    ]


def test_correlate_returns_all_commands(run_a, run_b):
    entries = correlate_runs(run_a, run_b)
    commands = {e.command for e in entries}
    assert commands == {"echo hello", "sleep 0.1", "ls /tmp", "date"}


def test_correlate_in_both_flag(run_a, run_b):
    entries = correlate_runs(run_a, run_b)
    idx = {e.command: e for e in entries}
    assert idx["echo hello"].in_both is True
    assert idx["ls /tmp"].in_both is False
    assert idx["date"].in_both is False


def test_correlate_delta_calculation(run_a, run_b):
    entries = correlate_runs(run_a, run_b)
    idx = {e.command: e for e in entries}
    entry = idx["echo hello"]
    assert entry.delta == pytest.approx(0.08 - 0.10, abs=1e-9)


def test_correlate_ratio_calculation(run_a, run_b):
    entries = correlate_runs(run_a, run_b)
    idx = {e.command: e for e in entries}
    entry = idx["sleep 0.1"]
    assert entry.ratio == pytest.approx(0.25 / 0.20, abs=1e-9)


def test_correlate_only_in_a_has_none_b(run_a, run_b):
    entries = correlate_runs(run_a, run_b)
    idx = {e.command: e for e in entries}
    assert idx["ls /tmp"].duration_b is None
    assert idx["ls /tmp"].ratio is None
    assert idx["ls /tmp"].delta is None


def test_correlate_only_in_b_has_none_a(run_a, run_b):
    entries = correlate_runs(run_a, run_b)
    idx = {e.command: e for e in entries}
    assert idx["date"].duration_a is None


def test_correlate_sorted_by_command(run_a, run_b):
    entries = correlate_runs(run_a, run_b)
    names = [e.command for e in entries]
    assert names == sorted(names)


def test_format_correlate_table_contains_header(run_a, run_b):
    entries = correlate_runs(run_a, run_b)
    table = format_correlate_table(entries)
    assert "Command" in table
    assert "Dur A" in table
    assert "Ratio" in table


def test_format_correlate_table_contains_commands(run_a, run_b):
    entries = correlate_runs(run_a, run_b)
    table = format_correlate_table(entries)
    assert "echo hello" in table
    assert "date" in table


def test_correlate_empty_runs():
    entries = correlate_runs([], [])
    assert entries == []
