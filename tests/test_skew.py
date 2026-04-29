"""Tests for batchmark.skew."""
import pytest
from batchmark.runner import CommandResult
from batchmark.skew import (
    SkewConfig,
    SkewEntry,
    detect_skew,
    parse_skew_config,
)


def make_result(command: str, duration: float, status: str = "success") -> CommandResult:
    return CommandResult(
        command=command,
        duration=duration,
        returncode=0 if status == "success" else 1,
        stdout="",
        stderr="",
        status=status,
    )


# --- parse_skew_config ---

def test_parse_skew_config_defaults():
    cfg = parse_skew_config({})
    assert cfg.threshold == 0.2
    assert cfg.min_runs == 3


def test_parse_skew_config_custom():
    cfg = parse_skew_config({"threshold": 0.5, "min_runs": 5})
    assert cfg.threshold == 0.5
    assert cfg.min_runs == 5


def test_parse_skew_config_invalid_threshold():
    with pytest.raises(ValueError, match="threshold"):
        parse_skew_config({"threshold": -0.1})


def test_parse_skew_config_invalid_min_runs():
    with pytest.raises(ValueError, match="min_runs"):
        parse_skew_config({"min_runs": 1})


# --- detect_skew ---

@pytest.fixture
def right_skewed_results():
    # most values low, one high outlier -> mean > median -> right skew
    return [
        make_result("cmd", 1.0),
        make_result("cmd", 1.0),
        make_result("cmd", 1.0),
        make_result("cmd", 1.1),
        make_result("cmd", 9.0),
    ]


def test_detect_skew_returns_one_entry_per_command(right_skewed_results):
    entries = detect_skew(right_skewed_results)
    assert len(entries) == 1
    assert entries[0].command == "cmd"


def test_detect_skew_right_direction(right_skewed_results):
    entry = detect_skew(right_skewed_results)[0]
    assert entry.direction == "right"
    assert entry.skew > 0


def test_detect_skew_flagged_above_threshold(right_skewed_results):
    cfg = SkewConfig(threshold=0.1)
    entry = detect_skew(right_skewed_results, config=cfg)[0]
    assert entry.flagged is True
    assert entry.reason is not None


def test_detect_skew_not_flagged_below_threshold():
    results = [make_result("cmd", float(v)) for v in [1.0, 1.0, 1.0, 1.0, 1.0]]
    entry = detect_skew(results)[0]
    assert entry.flagged is False
    assert entry.skew == 0.0
    assert entry.direction == "symmetric"


def test_detect_skew_too_few_runs_not_flagged():
    results = [make_result("cmd", 1.0), make_result("cmd", 5.0)]
    cfg = SkewConfig(min_runs=3)
    entry = detect_skew(results, config=cfg)[0]
    assert entry.flagged is False
    assert "too few runs" in (entry.reason or "")


def test_detect_skew_multiple_commands():
    results = [
        make_result("a", 1.0), make_result("a", 1.0), make_result("a", 5.0),
        make_result("b", 2.0), make_result("b", 2.0), make_result("b", 2.0),
    ]
    entries = detect_skew(results)
    cmds = {e.command for e in entries}
    assert cmds == {"a", "b"}


def test_detect_skew_run_count_correct(right_skewed_results):
    entry = detect_skew(right_skewed_results)[0]
    assert entry.run_count == 5


def test_detect_skew_left_direction():
    # most values high, one low outlier -> mean < median -> left skew
    results = [
        make_result("cmd", 9.0),
        make_result("cmd", 9.0),
        make_result("cmd", 9.0),
        make_result("cmd", 8.9),
        make_result("cmd", 1.0),
    ]
    entry = detect_skew(results)[0]
    assert entry.direction == "left"
    assert entry.skew < 0
