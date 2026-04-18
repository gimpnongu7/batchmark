"""Tests for batchmark.sort module."""

import pytest
from batchmark.runner import CommandResult
from batchmark.sort import sort_results, top_n


def make_result(cmd, duration, returncode=0):
    return CommandResult(
        command=cmd,
        returncode=returncode,
        stdout="",
        stderr="",
        duration=duration,
        timed_out=False,
    )


@pytest.fixture
def sample_results():
    return [
        make_result("cmd_c", 3.0),
        make_result("cmd_a", 1.0),
        make_result("cmd_b", 2.0, returncode=1),
    ]


def test_sort_by_duration_asc(sample_results):
    sorted_r = sort_results(sample_results, key="duration", reverse=False)
    durations = [r.duration for r in sorted_r]
    assert durations == [1.0, 2.0, 3.0]


def test_sort_by_duration_desc(sample_results):
    sorted_r = sort_results(sample_results, key="duration", reverse=True)
    assert sorted_r[0].duration == 3.0


def test_sort_by_command(sample_results):
    sorted_r = sort_results(sample_results, key="command")
    assert [r.command for r in sorted_r] == ["cmd_a", "cmd_b", "cmd_c"]


def test_sort_by_status(sample_results):
    sorted_r = sort_results(sample_results, key="status")
    # success (0) first
    assert sorted_r[0].returncode == 0
    assert sorted_r[-1].returncode == 1


def test_sort_invalid_key(sample_results):
    with pytest.raises(ValueError, match="Invalid sort key"):
        sort_results(sample_results, key="nonexistent")


def test_top_n_returns_correct_count(sample_results):
    result = top_n(sample_results, n=2)
    assert len(result) == 2


def test_top_n_slowest_first(sample_results):
    result = top_n(sample_results, n=2, key="duration", reverse=True)
    assert result[0].duration == 3.0


def test_top_n_invalid_n(sample_results):
    with pytest.raises(ValueError, match="n must be at least 1"):
        top_n(sample_results, n=0)
