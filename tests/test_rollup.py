import pytest
from batchmark.runner import CommandResult
from batchmark.rollup import (
    RollupConfig, parse_rollup_config, rollup, RollupGroup
)


def make_result(cmd, status="success", duration=1.0):
    return CommandResult(command=cmd, status=status, duration=duration,
                         stdout="", stderr="", returncode=0)


@pytest.fixture
def sample_results():
    return [
        make_result("build:frontend", "success", 1.0),
        make_result("build:backend", "success", 2.0),
        make_result("test:unit", "failure", 0.5),
        make_result("test:integration", "success", 3.0),
        make_result("lint:check", "failure", 0.2),
    ]


def test_rollup_by_status_keys(sample_results):
    groups = rollup(sample_results, RollupConfig(group_by="status"))
    names = {g.name for g in groups}
    assert "success" in names
    assert "failure" in names


def test_rollup_by_status_counts(sample_results):
    groups = rollup(sample_results, RollupConfig(group_by="status"))
    by_name = {g.name: g for g in groups}
    assert by_name["success"].command_count == 3
    assert by_name["failure"].command_count == 2


def test_rollup_by_prefix(sample_results):
    groups = rollup(sample_results, RollupConfig(group_by="prefix", prefix_delimiter=":"))
    names = {g.name for g in groups}
    assert "build" in names
    assert "test" in names
    assert "lint" in names


def test_rollup_success_rate(sample_results):
    groups = rollup(sample_results, RollupConfig(group_by="status"))
    by_name = {g.name: g for g in groups}
    assert by_name["success"].success_rate == 1.0
    assert by_name["failure"].success_rate == 0.0


def test_rollup_min_group_size_filters(sample_results):
    groups = rollup(sample_results, RollupConfig(group_by="prefix", min_group_size=2))
    names = {g.name for g in groups}
    assert "build" in names
    assert "test" in names
    assert "lint" not in names


def test_parse_rollup_config_defaults():
    cfg = parse_rollup_config({})
    assert cfg.group_by == "status"
    assert cfg.prefix_delimiter == ":"
    assert cfg.min_group_size == 1


def test_parse_rollup_config_full():
    cfg = parse_rollup_config({"group_by": "prefix", "prefix_delimiter": "/", "min_group_size": 3})
    assert cfg.group_by == "prefix"
    assert cfg.prefix_delimiter == "/"
    assert cfg.min_group_size == 3


def test_rollup_stats_present(sample_results):
    groups = rollup(sample_results, RollupConfig(group_by="status"))
    for g in groups:
        assert g.stats is not None
        assert g.stats.mean > 0
