import pytest
from batchmark.runner import CommandResult
from batchmark.histogram import (
    HistogramConfig,
    HistogramBin,
    parse_histogram_config,
    build_histogram,
)


def make_result(cmd: str, duration: float, status: str = "success") -> CommandResult:
    return CommandResult(command=cmd, duration=duration, returncode=0, stdout="", stderr="", status=status)


@pytest.fixture
def sample_results():
    return [
        make_result("a", 0.1),
        make_result("b", 0.3),
        make_result("c", 0.5),
        make_result("d", 0.7),
        make_result("e", 0.9),
    ]


def test_parse_histogram_config_defaults():
    cfg = parse_histogram_config({})
    assert cfg.bins == 10
    assert cfg.bar_width == 40
    assert cfg.min_duration is None
    assert cfg.max_duration is None


def test_parse_histogram_config_custom():
    cfg = parse_histogram_config({"bins": 5, "bar_width": 20, "min_duration": 0.0, "max_duration": 2.0})
    assert cfg.bins == 5
    assert cfg.bar_width == 20
    assert cfg.min_duration == 0.0
    assert cfg.max_duration == 2.0


def test_build_histogram_bin_count(sample_results):
    cfg = HistogramConfig(bins=5)
    bins = build_histogram(sample_results, cfg)
    assert len(bins) == 5


def test_build_histogram_total_count(sample_results):
    cfg = HistogramConfig(bins=5)
    bins = build_histogram(sample_results, cfg)
    assert sum(b.count for b in bins) == len(sample_results)


def test_build_histogram_empty_results():
    bins = build_histogram([], HistogramConfig())
    assert bins == []


def test_build_histogram_single_result():
    results = [make_result("x", 1.0)]
    bins = build_histogram(results, HistogramConfig(bins=4))
    assert sum(b.count for b in bins) == 1


def test_build_histogram_respects_max(sample_results):
    cfg = HistogramConfig(bins=5, max_duration=0.4)
    bins = build_histogram(sample_results, cfg)
    # only 0.1 and 0.3 are within range
    assert sum(b.count for b in bins) == 2


def test_build_histogram_commands_tracked(sample_results):
    cfg = HistogramConfig(bins=1)
    bins = build_histogram(sample_results, cfg)
    all_commands = [cmd for b in bins for cmd in b.commands]
    assert set(all_commands) == {"a", "b", "c", "d", "e"}


def test_bin_label_format():
    b = HistogramBin(low=0.1, high=0.5, count=3)
    assert "0.100" in b.label
    assert "0.500" in b.label
