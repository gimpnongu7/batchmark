"""Tests for batchmark.filter module."""

import pytest
from batchmark.runner import CommandResult
from batchmark.filter import filter_results, partition_results


def make_result(command, status, duration, returncode=0):
    return CommandResult(
        command=command,
        status=status,
        duration=duration,
        returncode=returncode,
        stdout="",
        stderr="",
    )


@pytest.fixture
def sample_results():
    return [
        make_result("echo hello", "success", 0.1),
        make_result("sleep 5", "timeout", 5.0, returncode=-1),
        make_result("false", "failure", 0.05, returncode=1),
        make_result("echo world", "success", 0.2),
        make_result("ls /tmp", "success", 0.3),
    ]


def test_filter_by_status(sample_results):
    result = filter_results(sample_results, status="success")
    assert len(result) == 3
    assert all(r.status == "success" for r in result)


def test_filter_by_min_duration(sample_results):
    result = filter_results(sample_results, min_duration=0.15)
    assert all(r.duration >= 0.15 for r in result)
    assert len(result) == 3


def test_filter_by_max_duration(sample_results):
    result = filter_results(sample_results, max_duration=0.2)
    assert all(r.duration <= 0.2 for r in result)


def test_filter_by_name_contains(sample_results):
    result = filter_results(sample_results, name_contains="echo")
    assert len(result) == 2
    assert all("echo" in r.command for r in result)


def test_filter_combined(sample_results):
    result = filter_results(sample_results, status="success", max_duration=0.15)
    assert len(result) == 1
    assert result[0].command == "echo hello"


def test_filter_no_criteria_returns_all(sample_results):
    result = filter_results(sample_results)
    assert len(result) == len(sample_results)


def test_partition_results(sample_results):
    successes, failures, timeouts = partition_results(sample_results)
    assert len(successes) == 3
    assert len(failures) == 1
    assert len(timeouts) == 1
