import pytest
from batchmark.runner import CommandResult
from batchmark.window import (
    WindowConfig, WindowSlice, sliding_windows, format_window_table, parse_window_config
)


def make_result(cmd, duration, rc=0):
    return CommandResult(command=cmd, duration=duration, returncode=rc, stdout="", stderr="")


@pytest.fixture
def sample_results():
    return [
        make_result("echo a", 0.1),
        make_result("echo b", 0.3),
        make_result("echo c", 0.2, rc=1),
        make_result("echo d", 0.4),
        make_result("echo e", 0.5),
        make_result("echo f", 0.6),
    ]


def test_sliding_windows_count(sample_results):
    cfg = WindowConfig(size=3, step=1)
    slices = sliding_windows(sample_results, cfg)
    assert len(slices) == 4


def test_sliding_windows_step2(sample_results):
    cfg = WindowConfig(size=3, step=2)
    slices = sliding_windows(sample_results, cfg)
    assert len(slices) == 2


def test_sliding_windows_mean_duration(sample_results):
    cfg = WindowConfig(size=3, step=3)
    slices = sliding_windows(sample_results, cfg)
    assert slices[0].mean_duration == pytest.approx((0.1 + 0.3 + 0.2) / 3)


def test_sliding_windows_success_rate(sample_results):
    cfg = WindowConfig(size=3, step=1)
    slices = sliding_windows(sample_results, cfg)
    # first window: a(0), b(0), c(1) -> 2/3
    assert slices[0].success_rate == pytest.approx(2 / 3)


def test_sliding_windows_commands_populated(sample_results):
    cfg = WindowConfig(size=2, step=2)
    slices = sliding_windows(sample_results, cfg)
    assert slices[0].commands == ["echo a", "echo b"]


def test_sliding_windows_min_fill_drops_partial(sample_results):
    cfg = WindowConfig(size=4, step=2, min_fill=1.0)
    slices = sliding_windows(sample_results, cfg)
    # windows starting at 0,2,4 — window at 4 has only 2 items, dropped
    assert all(len(s.results) == 4 for s in slices)


def test_sliding_windows_empty():
    assert sliding_windows([]) == []


def test_format_window_table_header(sample_results):
    cfg = WindowConfig(size=3, step=2)
    slices = sliding_windows(sample_results, cfg)
    table = format_window_table(slices)
    assert "Window" in table
    assert "Mean(s)" in table
    assert "Success%" in table


def test_format_window_table_empty():
    assert format_window_table([]) == "No window data."


def test_parse_window_config_defaults():
    cfg = parse_window_config({})
    assert cfg.size == 5
    assert cfg.step == 1
    assert cfg.min_fill == 1.0


def test_parse_window_config_values():
    cfg = parse_window_config({"window": {"size": 10, "step": 3, "min_fill": 0.5}})
    assert cfg.size == 10
    assert cfg.step == 3
    assert cfg.min_fill == 0.5
