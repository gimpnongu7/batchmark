"""Tests for batchmark.resample."""
import pytest
from batchmark.runner import CommandResult
from batchmark.resample import (
    ResampleConfig,
    ResampledResult,
    parse_resample_config,
    _snap,
    resample_results,
    resample_to_dicts,
)


def make_result(cmd: str, duration: float, status: str = "success") -> CommandResult:
    return CommandResult(command=cmd, duration=duration, status=status, stdout="", stderr="", returncode=0)


@pytest.fixture
def sample_results():
    return [
        make_result("echo a", 0.123),
        make_result("echo b", 0.456),
        make_result("echo c", 1.005),
        make_result("echo d", 0.0, status="failure"),
    ]


def test_snap_rounds_to_resolution():
    assert _snap(0.123, 0.1) == pytest.approx(0.1)
    assert _snap(0.456, 0.1) == pytest.approx(0.5)
    assert _snap(1.005, 0.1) == pytest.approx(1.0)


def test_snap_zero_resolution_raises():
    with pytest.raises(ValueError):
        _snap(0.5, 0.0)


def test_snap_fine_resolution():
    assert _snap(0.456, 0.01) == pytest.approx(0.46)


def test_parse_resample_config_defaults():
    cfg = parse_resample_config({})
    assert cfg.resolution == pytest.approx(0.1)
    assert cfg.min_duration == pytest.approx(0.0)
    assert cfg.max_duration is None


def test_parse_resample_config_full():
    cfg = parse_resample_config({"resolution": 0.05, "min_duration": 0.1, "max_duration": 5.0})
    assert cfg.resolution == pytest.approx(0.05)
    assert cfg.min_duration == pytest.approx(0.1)
    assert cfg.max_duration == pytest.approx(5.0)


def test_resample_results_count(sample_results):
    cfg = ResampleConfig(resolution=0.1)
    out = resample_results(sample_results, cfg)
    assert len(out) == len(sample_results)


def test_resample_results_snaps_duration(sample_results):
    cfg = ResampleConfig(resolution=0.1)
    out = resample_results(sample_results, cfg)
    assert out[0].resampled_duration == pytest.approx(0.1)
    assert out[1].resampled_duration == pytest.approx(0.5)


def test_resample_respects_min_duration():
    results = [make_result("cmd", 0.0)]
    cfg = ResampleConfig(resolution=0.1, min_duration=0.2)
    out = resample_results(results, cfg)
    assert out[0].resampled_duration == pytest.approx(0.2)


def test_resample_respects_max_duration():
    results = [make_result("cmd", 10.0)]
    cfg = ResampleConfig(resolution=1.0, max_duration=5.0)
    out = resample_results(results, cfg)
    assert out[0].resampled_duration == pytest.approx(5.0)


def test_resample_preserves_original():
    r = make_result("echo x", 0.777)
    cfg = ResampleConfig(resolution=0.1)
    out = resample_results([r], cfg)
    assert out[0].original.duration == pytest.approx(0.777)
    assert out[0].original is r


def test_resample_to_dicts_keys(sample_results):
    cfg = ResampleConfig(resolution=0.1)
    out = resample_results(sample_results, cfg)
    dicts = resample_to_dicts(out)
    assert set(dicts[0].keys()) == {"command", "status", "original_duration", "resampled_duration"}


def test_resample_to_dicts_values(sample_results):
    cfg = ResampleConfig(resolution=0.1)
    out = resample_results(sample_results, cfg)
    dicts = resample_to_dicts(out)
    assert dicts[0]["command"] == "echo a"
    assert dicts[0]["original_duration"] == pytest.approx(0.123)
    assert dicts[0]["resampled_duration"] == pytest.approx(0.1)
