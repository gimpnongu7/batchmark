import pytest
from batchmark.runner import CommandResult
from batchmark.summarize import summarize, format_summary


def make_result(cmd, status="success", duration=1.0, exit_code=0):
    return CommandResult(
        command=cmd,
        status=status,
        exit_code=exit_code if status != "timeout" else None,
        duration=duration,
        stdout="",
        stderr="",
    )


@pytest.fixture
def sample_results():
    return [
        make_result("echo a", duration=0.1),
        make_result("sleep 1", duration=1.5),
        make_result("false", status="failure", duration=0.2, exit_code=1),
        make_result("timeout_cmd", status="timeout", duration=5.0),
    ]


def test_summarize_counts(sample_results):
    s = summarize(sample_results)
    assert s.total == 4
    assert s.passed == 2
    assert s.failed == 1
    assert s.timed_out == 1


def test_summarize_fastest_slowest(sample_results):
    s = summarize(sample_results)
    assert s.fastest_cmd == "echo a"
    assert s.slowest_cmd == "timeout_cmd"


def test_summarize_stats_present(sample_results):
    s = summarize(sample_results)
    assert s.stats.mean > 0
    assert s.stats.median > 0


def test_summarize_empty_raises():
    with pytest.raises(ValueError, match="No results"):
        summarize([])


def test_format_summary_contains_fields(sample_results):
    s = summarize(sample_results)
    out = format_summary(s)
    assert "Run Summary" in out
    assert "Passed" in out
    assert "Failed" in out
    assert "Timed out" in out
    assert "echo a" in out
    assert "timeout_cmd" in out
    assert "Mean" in out


def test_format_summary_single_result():
    results = [make_result("ls", duration=0.05)]
    s = summarize(results)
    out = format_summary(s)
    assert "ls" in out
    assert s.fastest_cmd == s.slowest_cmd == "ls"
