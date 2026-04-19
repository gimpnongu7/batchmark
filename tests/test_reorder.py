import pytest
from batchmark.runner import CommandResult
from batchmark.reorder import (
    ReorderConfig,
    parse_reorder_config,
    reorder_results,
    move_to_back,
)


def make_result(cmd, duration=1.0, status="success"):
    return CommandResult(command=cmd, returncode=0, stdout="", stderr="", duration=duration, status=status)


@pytest.fixture
def sample_results():
    return [
        make_result("echo a"),
        make_result("echo b"),
        make_result("echo c"),
        make_result("echo d"),
    ]


def test_parse_reorder_config_defaults():
    cfg = parse_reorder_config({"priority": ["echo a"]})
    assert cfg.priority == ["echo a"]
    assert cfg.reverse is False
    assert cfg.stable is True


def test_parse_reorder_config_full():
    cfg = parse_reorder_config({"priority": ["x"], "reverse": True, "stable": False})
    assert cfg.reverse is True
    assert cfg.stable is False


def test_reorder_moves_priority_to_front(sample_results):
    cfg = ReorderConfig(priority=["echo c", "echo a"])
    out = reorder_results(sample_results, cfg)
    assert out[0].command == "echo c"
    assert out[1].command == "echo a"


def test_reorder_preserves_priority_order(sample_results):
    cfg = ReorderConfig(priority=["echo d", "echo b"])
    out = reorder_results(sample_results, cfg)
    assert out[0].command == "echo d"
    assert out[1].command == "echo b"


def test_reorder_rest_unchanged(sample_results):
    cfg = ReorderConfig(priority=["echo a"])
    out = reorder_results(sample_results, cfg)
    rest = [r.command for r in out[1:]]
    assert rest == ["echo b", "echo c", "echo d"]


def test_reorder_reverse(sample_results):
    cfg = ReorderConfig(priority=[], reverse=True)
    out = reorder_results(sample_results, cfg)
    assert [r.command for r in out] == ["echo d", "echo c", "echo b", "echo a"]


def test_reorder_empty_priority(sample_results):
    cfg = ReorderConfig(priority=[])
    out = reorder_results(sample_results, cfg)
    assert [r.command for r in out] == [r.command for r in sample_results]


def test_move_to_back(sample_results):
    out = move_to_back(sample_results, ["echo b", "echo d"])
    commands = [r.command for r in out]
    assert commands == ["echo a", "echo c", "echo b", "echo d"]


def test_move_to_back_unknown_command(sample_results):
    out = move_to_back(sample_results, ["echo z"])
    assert len(out) == len(sample_results)
