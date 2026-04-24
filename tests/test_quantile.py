"""Tests for batchmark.quantile."""
import pytest
from batchmark.runner import CommandResult
from batchmark.quantile import (
    QuantileConfig,
    QuantileEntry,
    parse_quantile_config,
    compute_quantiles,
    _quantile_label,
)


def make_result(command: str, duration: float, status: str = "success") -> CommandResult:
    return CommandResult(command=command, duration=duration, status=status, stdout="", stderr="", returncode=0)


@pytest.fixture
def sample_results():
    return [
        make_result("echo hi", 0.1),
        make_result("echo hi", 0.2),
        make_result("echo hi", 0.3),
        make_result("echo hi", 0.4),
        make_result("echo hi", 0.5),
        make_result("sleep 1", 1.0),
        make_result("sleep 1", 1.2),
        make_result("sleep 1", 0.9),
    ]


def test_parse_quantile_config_defaults():
    cfg = parse_quantile_config({})
    assert 0.50 in cfg.quantiles
    assert 0.95 in cfg.quantiles
    assert cfg.include_failures is False


def test_parse_quantile_config_custom():
    cfg = parse_quantile_config({"quantiles": [0.5, 0.9], "include_failures": True})
    assert cfg.quantiles == [0.5, 0.9]
    assert cfg.include_failures is True


def test_parse_quantile_config_invalid_raises():
    with pytest.raises(ValueError):
        parse_quantile_config({"quantiles": [1.5]})


def test_quantile_label_p50():
    assert _quantile_label(0.50) == "p50"


def test_quantile_label_p99():
    assert _quantile_label(0.99) == "p99"


def test_compute_quantiles_returns_entries(sample_results):
    cfg = QuantileConfig(quantiles=[0.50])
    entries = compute_quantiles(sample_results, cfg)
    commands = {e.command for e in entries}
    assert "echo hi" in commands
    assert "sleep 1" in commands


def test_compute_quantiles_count(sample_results):
    cfg = QuantileConfig(quantiles=[0.25, 0.50, 0.75])
    entries = compute_quantiles(sample_results, cfg)
    echo_entries = [e for e in entries if e.command == "echo hi"]
    assert len(echo_entries) == 3


def test_compute_quantiles_median_value():
    results = [make_result("cmd", float(d)) for d in [1, 2, 3, 4, 5]]
    cfg = QuantileConfig(quantiles=[0.50])
    entries = compute_quantiles(results, cfg)
    assert len(entries) == 1
    assert entries[0].value == pytest.approx(3.0)


def test_compute_quantiles_excludes_failures_by_default():
    results = [
        make_result("cmd", 1.0, "success"),
        make_result("cmd", 99.0, "failure"),
    ]
    cfg = QuantileConfig(quantiles=[0.50])
    entries = compute_quantiles(results, cfg)
    assert entries[0].value == pytest.approx(1.0)


def test_compute_quantiles_includes_failures_when_enabled():
    results = [
        make_result("cmd", 1.0, "success"),
        make_result("cmd", 99.0, "failure"),
    ]
    cfg = QuantileConfig(quantiles=[0.50], include_failures=True)
    entries = compute_quantiles(results, cfg)
    assert entries[0].value == pytest.approx(50.0)


def test_compute_quantiles_single_result():
    results = [make_result("cmd", 2.5)]
    cfg = QuantileConfig(quantiles=[0.25, 0.75])
    entries = compute_quantiles(results, cfg)
    assert all(e.value == pytest.approx(2.5) for e in entries)


def test_compute_quantiles_label_assigned():
    results = [make_result("cmd", 1.0), make_result("cmd", 2.0)]
    cfg = QuantileConfig(quantiles=[0.95])
    entries = compute_quantiles(results, cfg)
    assert entries[0].label == "p95"
