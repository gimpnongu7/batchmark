"""Tests for batchmark.absorb."""
import pytest
from batchmark.runner import CommandResult
from batchmark.absorb import (
    AbsorbConfig,
    AbsorbedGroup,
    parse_absorb_config,
    absorb_results,
)


def make_result(cmd: str, duration: float, status: str = "success") -> CommandResult:
    return CommandResult(command=cmd, duration=duration, status=status, stdout="", stderr="", returncode=0)


@pytest.fixture
def sample_results():
    return [
        make_result("echo a", 0.10),
        make_result("echo a", 0.11),  # within 0.5s gap of prev
        make_result("echo a", 0.80),  # outside gap
        make_result("echo b", 0.20),
        make_result("echo b", 0.25),
    ]


def test_parse_absorb_config_defaults():
    cfg = parse_absorb_config({})
    assert cfg.gap_seconds == 0.5
    assert cfg.strategy == "fastest"
    assert cfg.include_absorbed is False


def test_parse_absorb_config_custom():
    cfg = parse_absorb_config({"absorb": {"gap_seconds": 1.0, "strategy": "last", "include_absorbed": True}})
    assert cfg.gap_seconds == 1.0
    assert cfg.strategy == "last"
    assert cfg.include_absorbed is True


def test_parse_absorb_config_invalid_strategy():
    with pytest.raises(ValueError, match="strategy"):
        parse_absorb_config({"absorb": {"strategy": "median"}})


def test_parse_absorb_config_negative_gap():
    with pytest.raises(ValueError, match="gap_seconds"):
        parse_absorb_config({"absorb": {"gap_seconds": -0.1}})


def test_absorb_empty_returns_empty():
    assert absorb_results([]) == []


def test_absorb_groups_close_durations(sample_results):
    cfg = AbsorbConfig(gap_seconds=0.5, strategy="fastest")
    groups = absorb_results(sample_results, cfg)
    # echo a: [0.10, 0.11] absorbed together, 0.80 separate; echo b: [0.20, 0.25] absorbed
    assert len(groups) == 3


def test_absorb_fastest_picks_min(sample_results):
    cfg = AbsorbConfig(gap_seconds=0.5, strategy="fastest")
    groups = absorb_results(sample_results, cfg)
    first_group = groups[0]
    assert first_group.duration == pytest.approx(0.10)


def test_absorb_first_strategy():
    results = [make_result("cmd", 0.3), make_result("cmd", 0.1)]
    cfg = AbsorbConfig(gap_seconds=1.0, strategy="first")
    groups = absorb_results(results, cfg)
    assert len(groups) == 1
    assert groups[0].duration == pytest.approx(0.3)


def test_absorb_last_strategy():
    results = [make_result("cmd", 0.3), make_result("cmd", 0.1)]
    cfg = AbsorbConfig(gap_seconds=1.0, strategy="last")
    groups = absorb_results(results, cfg)
    assert len(groups) == 1
    assert groups[0].duration == pytest.approx(0.1)


def test_absorb_total_absorbed_count(sample_results):
    cfg = AbsorbConfig(gap_seconds=0.5, strategy="fastest")
    groups = absorb_results(sample_results, cfg)
    first = groups[0]
    assert first.total_absorbed == 1  # one sibling absorbed


def test_absorb_different_commands_not_merged():
    results = [make_result("echo a", 0.1), make_result("echo b", 0.1)]
    cfg = AbsorbConfig(gap_seconds=1.0, strategy="fastest")
    groups = absorb_results(results, cfg)
    assert len(groups) == 2


def test_absorbed_group_command_property():
    r = make_result("ls", 0.05)
    g = AbsorbedGroup(representative=r)
    assert g.command == "ls"
    assert g.duration == pytest.approx(0.05)
