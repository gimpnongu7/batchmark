import pytest
from batchmark.runner import CommandResult
from batchmark.clamp import (
    ClampConfig,
    parse_clamp_config,
    clamp_duration,
    clamp_results,
)


def make_result(cmd="echo hi", duration=1.0, rc=0):
    return CommandResult(
        command=cmd,
        returncode=rc,
        stdout="",
        stderr="",
        duration=duration,
        timed_out=False,
    )


def test_clamp_duration_no_limits():
    cfg = ClampConfig()
    assert clamp_duration(5.0, cfg) == 5.0


def test_clamp_duration_min():
    cfg = ClampConfig(min_duration=2.0)
    assert clamp_duration(0.5, cfg) == 2.0


def test_clamp_duration_max():
    cfg = ClampConfig(max_duration=3.0)
    assert clamp_duration(10.0, cfg) == 3.0


def test_clamp_duration_within_range():
    cfg = ClampConfig(min_duration=1.0, max_duration=5.0)
    assert clamp_duration(3.0, cfg) == 3.0


def test_clamp_duration_below_min():
    cfg = ClampConfig(min_duration=1.0, max_duration=5.0)
    assert clamp_duration(0.1, cfg) == 1.0


def test_clamp_duration_above_max():
    cfg = ClampConfig(min_duration=1.0, max_duration=5.0)
    assert clamp_duration(9.9, cfg) == 5.0


def test_clamp_results_replaces_duration():
    results = [make_result(duration=0.1), make_result(duration=8.0)]
    cfg = ClampConfig(min_duration=0.5, max_duration=5.0)
    out = clamp_results(results, cfg)
    assert out[0].duration == 0.5
    assert out[1].duration == 5.0


def test_clamp_results_preserves_unchanged():
    results = [make_result(duration=2.0)]
    cfg = ClampConfig(min_duration=1.0, max_duration=3.0)
    out = clamp_results(results, cfg)
    assert out[0] is results[0]


def test_clamp_results_preserves_other_fields():
    r = make_result(cmd="ls", duration=0.0, rc=1)
    cfg = ClampConfig(min_duration=0.5)
    out = clamp_results([r], cfg)
    assert out[0].command == "ls"
    assert out[0].returncode == 1


def test_parse_clamp_config_defaults():
    cfg = parse_clamp_config({})
    assert cfg.min_duration is None
    assert cfg.max_duration is None


def test_parse_clamp_config_full():
    raw = {"clamp": {"min_duration": 0.2, "max_duration": 10.0}}
    cfg = parse_clamp_config(raw)
    assert cfg.min_duration == 0.2
    assert cfg.max_duration == 10.0
