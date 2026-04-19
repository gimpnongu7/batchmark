import pytest
from batchmark.runner import CommandResult
from batchmark.normalize import (
    NormalizeConfig,
    normalize_durations,
    parse_normalize_config,
)


def make_result(cmd, duration, status="success", rc=0):
    return CommandResult(command=cmd, status=status, duration=duration,
                         returncode=rc, stdout="", stderr="")


@pytest.fixture
def sample_results():
    return [
        make_result("cmd_a", 1.0),
        make_result("cmd_b", 3.0),
        make_result("cmd_c", 5.0),
    ]


def test_min_max_range(sample_results):
    out = normalize_durations(sample_results)
    scores = [r["normalized_duration"] for r in out]
    assert min(scores) == pytest.approx(0.0)
    assert max(scores) == pytest.approx(1.0)


def test_min_max_middle_value(sample_results):
    out = normalize_durations(sample_results)
    assert out[1]["normalized_duration"] == pytest.approx(0.5)


def test_min_max_custom_floor_ceiling(sample_results):
    cfg = NormalizeConfig(method="min-max", floor=0.2, ceiling=0.8)
    out = normalize_durations(sample_results, cfg)
    scores = [r["normalized_duration"] for r in out]
    assert min(scores) == pytest.approx(0.2)
    assert max(scores) == pytest.approx(0.8)


def test_z_score_mean_is_zero(sample_results):
    cfg = NormalizeConfig(method="z-score")
    out = normalize_durations(sample_results, cfg)
    scores = [r["normalized_duration"] for r in out]
    assert sum(scores) == pytest.approx(0.0, abs=1e-9)


def test_z_score_identical_durations():
    results = [make_result("a", 2.0), make_result("b", 2.0)]
    cfg = NormalizeConfig(method="z-score")
    out = normalize_durations(results, cfg)
    assert all(r["normalized_duration"] == 0.0 for r in out)


def test_min_max_identical_durations():
    results = [make_result("a", 4.0), make_result("b", 4.0)]
    out = normalize_durations(results)
    assert all(r["normalized_duration"] == 0.0 for r in out)


def test_empty_results():
    assert normalize_durations([]) == []


def test_output_keys(sample_results):
    out = normalize_durations(sample_results)
    for row in out:
        assert "command" in row
        assert "normalized_duration" in row
        assert "duration" in row


def test_parse_normalize_config_defaults():
    cfg = parse_normalize_config({})
    assert cfg.method == "min-max"
    assert cfg.floor == 0.0
    assert cfg.ceiling == 1.0


def test_parse_normalize_config_full():
    raw = {"normalize": {"method": "z-score", "floor": -1.0, "ceiling": 1.0}}
    cfg = parse_normalize_config(raw)
    assert cfg.method == "z-score"
    assert cfg.floor == -1.0
