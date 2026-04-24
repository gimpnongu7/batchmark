"""Tests for batchmark.velocity."""
import pytest
from batchmark.runner import CommandResult
from batchmark.velocity import (
    VelocityConfig,
    VelocityEntry,
    parse_velocity_config,
    compute_velocity,
)


def make_result(cmd: str, duration: float, status: str = "success") -> CommandResult:
    return CommandResult(command=cmd, duration=duration, returncode=0, stdout="", stderr="", status=status)


@pytest.fixture
def sample_results():
    return [
        make_result("cmd_a", 1.0),
        make_result("cmd_b", 2.0),
        make_result("cmd_c", 1.0),
        make_result("cmd_d", 3.0),
        make_result("cmd_e", 1.0),
    ]


def test_parse_velocity_config_defaults():
    cfg = parse_velocity_config({})
    assert cfg.window == 10
    assert cfg.min_samples == 2


def test_parse_velocity_config_custom():
    cfg = parse_velocity_config({"window": 3, "min_samples": 1})
    assert cfg.window == 3
    assert cfg.min_samples == 1


def test_compute_velocity_returns_one_per_result(sample_results):
    entries = compute_velocity(sample_results)
    assert len(entries) == len(sample_results)


def test_compute_velocity_index_matches(sample_results):
    entries = compute_velocity(sample_results)
    for i, e in enumerate(entries):
        assert e.index == i


def test_compute_velocity_command_matches(sample_results):
    entries = compute_velocity(sample_results)
    for r, e in zip(sample_results, entries):
        assert e.command == r.command


def test_compute_velocity_none_before_min_samples():
    results = [make_result("x", 1.0)]
    cfg = VelocityConfig(min_samples=2)
    entries = compute_velocity(results, cfg)
    assert entries[0].rolling_velocity is None
    assert entries[0].cumulative_velocity is None


def test_compute_velocity_cumulative_after_min_samples(sample_results):
    cfg = VelocityConfig(min_samples=2)
    entries = compute_velocity(sample_results, cfg)
    # after 2 results: 2 commands / (1.0+2.0) sec = 0.666...
    assert entries[1].cumulative_velocity == pytest.approx(2 / 3.0, rel=1e-4)


def test_compute_velocity_rolling_uses_window():
    results = [make_result(f"c{i}", 1.0) for i in range(6)]
    cfg = VelocityConfig(window=3, min_samples=2)
    entries = compute_velocity(results, cfg)
    # window of last 3, each 1.0s: 3 / 3.0 = 1.0 cmd/s
    assert entries[5].rolling_velocity == pytest.approx(1.0)


def test_is_accelerating_true():
    # rolling faster than cumulative
    e = VelocityEntry(index=5, command="x", duration=0.5, rolling_velocity=3.0, cumulative_velocity=1.0)
    assert e.is_accelerating is True


def test_is_accelerating_false():
    e = VelocityEntry(index=5, command="x", duration=2.0, rolling_velocity=0.5, cumulative_velocity=1.5)
    assert e.is_accelerating is False


def test_is_accelerating_none_when_no_data():
    e = VelocityEntry(index=0, command="x", duration=1.0, rolling_velocity=None, cumulative_velocity=None)
    assert e.is_accelerating is None
