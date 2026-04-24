"""Tests for batchmark.floor."""

import pytest
from batchmark.runner import CommandResult
from batchmark.floor import (
    FloorConfig,
    parse_floor_config,
    floor_duration,
    floor_results,
    floor_summary,
)


def make_result(cmd: str, duration: float, rc: int = 0) -> CommandResult:
    return CommandResult(
        command=cmd,
        returncode=rc,
        stdout="",
        stderr="",
        duration=duration,
        timed_out=False,
    )


# --- parse_floor_config ---

def test_parse_floor_config_defaults():
    cfg = parse_floor_config({})
    assert cfg.resolution == 0.1
    assert cfg.min_duration is None


def test_parse_floor_config_custom():
    cfg = parse_floor_config({"resolution": 0.5, "min_duration": 0.05})
    assert cfg.resolution == 0.5
    assert cfg.min_duration == 0.05


def test_parse_floor_config_invalid_resolution():
    with pytest.raises(ValueError, match="resolution must be > 0"):
        parse_floor_config({"resolution": 0})


def test_parse_floor_config_negative_resolution():
    with pytest.raises(ValueError):
        parse_floor_config({"resolution": -1.0})


# --- floor_duration ---

def test_floor_duration_already_on_boundary():
    cfg = FloorConfig(resolution=0.1)
    assert floor_duration(0.3, cfg) == pytest.approx(0.3)


def test_floor_duration_rounds_down():
    cfg = FloorConfig(resolution=0.1)
    assert floor_duration(0.37, cfg) == pytest.approx(0.3)


def test_floor_duration_large_resolution():
    cfg = FloorConfig(resolution=1.0)
    assert floor_duration(2.99, cfg) == pytest.approx(2.0)


def test_floor_duration_respects_min_duration():
    cfg = FloorConfig(resolution=0.1, min_duration=0.5)
    # 0.23 floored to 0.2, but min is 0.5
    assert floor_duration(0.23, cfg) == pytest.approx(0.5)


def test_floor_duration_min_not_triggered():
    cfg = FloorConfig(resolution=0.1, min_duration=0.1)
    assert floor_duration(0.85, cfg) == pytest.approx(0.8)


# --- floor_results ---

@pytest.fixture
def sample_results():
    return [
        make_result("echo a", 0.37),
        make_result("echo b", 1.99),
        make_result("echo c", 0.10),
    ]


def test_floor_results_count(sample_results):
    cfg = FloorConfig(resolution=0.1)
    out = floor_results(sample_results, cfg)
    assert len(out) == len(sample_results)


def test_floor_results_values(sample_results):
    cfg = FloorConfig(resolution=0.1)
    out = floor_results(sample_results, cfg)
    assert out[0].duration == pytest.approx(0.3)
    assert out[1].duration == pytest.approx(1.9)
    assert out[2].duration == pytest.approx(0.1)


def test_floor_results_preserves_command(sample_results):
    cfg = FloorConfig(resolution=0.1)
    out = floor_results(sample_results, cfg)
    assert [r.command for r in out] == [r.command for r in sample_results]


# --- floor_summary ---

def test_floor_summary_count(sample_results):
    cfg = FloorConfig(resolution=0.1)
    floored = floor_results(sample_results, cfg)
    s = floor_summary(sample_results, floored)
    assert s["count"] == 3


def test_floor_summary_total_shaved(sample_results):
    cfg = FloorConfig(resolution=0.1)
    floored = floor_results(sample_results, cfg)
    s = floor_summary(sample_results, floored)
    # 0.07 + 0.09 + 0.00 = 0.16
    assert s["total_shaved"] == pytest.approx(0.16, abs=1e-9)
