import pytest
from batchmark.runner import CommandResult
from batchmark.group import group_by, group_by_fn, format_group_table, GroupEntry


def make_result(cmd="echo hi", status="success", duration=1.0):
    return CommandResult(command=cmd, status=status, duration=duration, stdout="", stderr="", returncode=0)


@pytest.fixture
def sample_results():
    return [
        make_result("cmd_a", "success", 1.0),
        make_result("cmd_b", "success", 2.0),
        make_result("cmd_c", "failure", 0.5),
        make_result("cmd_a", "failure", 3.0),
    ]


def test_group_by_status_keys(sample_results):
    groups = group_by(sample_results, "status")
    assert set(groups.keys()) == {"success", "failure"}


def test_group_by_status_counts(sample_results):
    groups = group_by(sample_results, "status")
    assert groups["success"].stats.total == 2
    assert groups["failure"].stats.total == 2


def test_group_by_command(sample_results):
    groups = group_by(sample_results, "command")
    assert "cmd_a" in groups
    assert len(groups["cmd_a"].results) == 2


def test_group_entry_stats_mean():
    results = [make_result(duration=1.0), make_result(duration=3.0)]
    entry = GroupEntry(name="test", results=results)
    assert entry.stats.mean == pytest.approx(2.0)


def test_group_by_fn(sample_results):
    groups = group_by_fn(sample_results, lambda r: "fast" if r.duration < 2.0 else "slow")
    assert "fast" in groups
    assert "slow" in groups
    assert groups["fast"].stats.total == 2


def test_format_group_table_contains_group_names(sample_results):
    groups = group_by(sample_results, "status")
    table = format_group_table(groups)
    assert "success" in table
    assert "failure" in table


def test_format_group_table_contains_header(sample_results):
    groups = group_by(sample_results, "status")
    table = format_group_table(groups)
    assert "Group" in table
    assert "Mean" in table
