"""Tests for batchmark.stats module."""
import pytest
from batchmark.runner import CommandResult
from batchmark.stats import compute_stats, stats_to_dict


def make_result(cmd, exit_code, duration, timed_out=False):
    return CommandResult(command=cmd, exit_code=exit_code, duration=duration,
                         stdout="", stderr="", timed_out=timed_out)


@pytest.fixture
def sample_results():
    return [
        make_result("echo a", 0, 0.1),
        make_result("echo b", 0, 0.3),
        make_result("false", 1, 0.2),
        make_result("sleep 10", 1, 5.0, timed_out=True),
        make_result("echo c", 0, 0.15),
    ]


def test_compute_stats_counts(sample_results):
    stats = compute_stats(sample_results)
    assert stats.count == 5
    assert stats.success_count == 3
    assert stats.failure_count == 2
    assert stats.timeout_count == 1


def test_compute_stats_duration(sample_results):
    stats = compute_stats(sample_results)
    assert stats.min_duration == pytest.approx(0.1)
    assert stats.max_duration == pytest.approx(5.0)
    assert stats.mean_duration == pytest.approx((0.1 + 0.3 + 0.2 + 5.0 + 0.15) / 5, rel=1e-3)


def test_compute_stats_median_odd(sample_results):
    stats = compute_stats(sample_results)
    # sorted: 0.1, 0.15, 0.2, 0.3, 5.0 -> median = 0.2
    assert stats.median_duration == pytest.approx(0.2)


def test_compute_stats_median_even():
    results = [
        make_result("a", 0, 1.0),
        make_result("b", 0, 2.0),
        make_result("c", 0, 3.0),
        make_result("d", 0, 4.0),
    ]
    stats = compute_stats(results)
    assert stats.median_duration == pytest.approx(2.5)


def test_compute_stats_empty_raises():
    with pytest.raises(ValueError, match="empty"):
        compute_stats([])


def test_stats_to_dict_keys(sample_results):
    d = stats_to_dict(compute_stats(sample_results))
    expected_keys = {"count", "success_count", "failure_count", "timeout_count",
                     "min_duration", "max_duration", "mean_duration", "median_duration",
                     "p95_duration"}
    assert set(d.keys()) == expected_keys
