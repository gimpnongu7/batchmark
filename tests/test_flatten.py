import pytest
from batchmark.runner import CommandResult
from batchmark.flatten import (
    FlattenConfig,
    flatten_groups,
    flatten_with_tags,
    parse_flatten_config,
)


def make_result(cmd="echo hi", rc=0, duration=0.1):
    return CommandResult(
        command=cmd,
        returncode=rc,
        duration=duration,
        stdout="",
        stderr="",
        timed_out=False,
    )


@pytest.fixture
def groups():
    return {
        "fast": [make_result("echo a", duration=0.1), make_result("echo b", duration=0.2)],
        "slow": [make_result("sleep 1", duration=1.0)],
    }


def test_flatten_groups_total_count(groups):
    result = flatten_groups(groups)
    assert len(result) == 3


def test_flatten_groups_returns_command_results(groups):
    result = flatten_groups(groups)
    assert all(isinstance(r, CommandResult) for r in result)


def test_flatten_groups_preserves_order(groups):
    result = flatten_groups(groups)
    assert result[0].command == "echo a"
    assert result[1].command == "echo b"
    assert result[2].command == "sleep 1"


def test_flatten_with_tags_adds_source(groups):
    cfg = FlattenConfig(add_source_tag=True, source_key="source")
    out = flatten_with_tags(groups, cfg)
    assert out[0]["source"] == "fast"
    assert out[2]["source"] == "slow"


def test_flatten_with_tags_custom_key(groups):
    cfg = FlattenConfig(add_source_tag=True, source_key="group")
    out = flatten_with_tags(groups, cfg)
    assert "group" in out[0]
    assert out[0]["group"] == "fast"


def test_flatten_with_tags_no_source(groups):
    cfg = FlattenConfig(add_source_tag=False)
    out = flatten_with_tags(groups, cfg)
    assert "source" not in out[0]


def test_flatten_with_tags_has_expected_keys(groups):
    out = flatten_with_tags(groups)
    keys = set(out[0].keys())
    assert {"command", "returncode", "duration", "stdout", "stderr", "timed_out", "source"} == keys


def test_parse_flatten_config_defaults():
    cfg = parse_flatten_config({})
    assert cfg.add_source_tag is True
    assert cfg.source_key == "source"


def test_parse_flatten_config_custom():
    cfg = parse_flatten_config({"flatten": {"add_source_tag": False, "source_key": "batch"}})
    assert cfg.add_source_tag is False
    assert cfg.source_key == "batch"
