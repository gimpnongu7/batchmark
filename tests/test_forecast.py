"""Tests for batchmark.forecast."""
import pytest
from batchmark.runner import CommandResult
from batchmark.forecast import (
    ForecastConfig,
    ForecastEntry,
    forecast,
    parse_forecast_config,
    _trend_label,
)


def make_result(cmd: str, duration: float, status: str = "success") -> CommandResult:
    return CommandResult(command=cmd, duration=duration, returncode=0, stdout="", stderr="", status=status)


@pytest.fixture
def sample_results():
    return [
        make_result("echo a", 1.0),
        make_result("echo a", 1.1),
        make_result("echo a", 1.2),
        make_result("echo b", 0.5),
        make_result("echo b", 0.6),
    ]


def test_parse_forecast_config_defaults():
    cfg = parse_forecast_config({})
    assert cfg.window == 5
    assert cfg.trend_threshold == 0.10


def test_parse_forecast_config_custom():
    cfg = parse_forecast_config({"window": 3, "trend_threshold": 0.05})
    assert cfg.window == 3
    assert cfg.trend_threshold == 0.05


def test_forecast_returns_one_entry_per_command(sample_results):
    entries = forecast(sample_results, ForecastConfig())
    commands = {e.command for e in entries}
    assert commands == {"echo a", "echo b"}


def test_forecast_sample_count(sample_results):
    entries = {e.command: e for e in forecast(sample_results, ForecastConfig())}
    assert entries["echo a"].sample_count == 3
    assert entries["echo b"].sample_count == 2


def test_forecast_mean_duration(sample_results):
    entries = {e.command: e for e in forecast(sample_results, ForecastConfig())}
    assert abs(entries["echo a"].mean_duration - 1.1) < 0.001


def test_forecast_window_limits_samples():
    results = [make_result("cmd", float(i)) for i in range(1, 11)]
    cfg = ForecastConfig(window=3)
    entries = forecast(results, cfg)
    assert entries[0].sample_count == 3
    assert abs(entries[0].mean_duration - 9.0) < 0.001


def test_trend_label_stable():
    assert _trend_label(1.0, 1.05, 0.10) == "stable"


def test_trend_label_degrading():
    assert _trend_label(1.0, 1.5, 0.10) == "degrading"


def test_trend_label_improving():
    assert _trend_label(1.0, 0.5, 0.10) == "improving"


def test_trend_label_zero_early():
    assert _trend_label(0.0, 1.0, 0.10) == "stable"


def test_forecast_stable_trend():
    results = [make_result("cmd", 1.0) for _ in range(4)]
    entries = forecast(results, ForecastConfig())
    assert entries[0].trend == "stable"


def test_forecast_empty_results():
    """forecast() with no results should return an empty list."""
    entries = forecast([], ForecastConfig())
    assert entries == []


def test_forecast_single_result():
    """A single result should produce one entry with sample_count=1 and stable trend."""
    results = [make_result("solo", 2.5)]
    entries = forecast(results, ForecastConfig())
    assert len(entries) == 1
    assert entries[0].command == "solo"
    assert entries[0].sample_count == 1
    assert abs(entries[0].mean_duration - 2.5) < 0.001
    assert entries[0].trend == "stable"
