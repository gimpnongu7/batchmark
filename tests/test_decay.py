"""Tests for batchmark.decay and batchmark.decay_report."""
import json
import pytest

from batchmark.runner import CommandResult
from batchmark.decay import (
    DecayConfig,
    DecayEntry,
    parse_decay_config,
    apply_decay,
    _weight,
)
from batchmark.decay_report import (
    entry_to_dict,
    format_decay_json,
    format_decay_table,
    decay_summary,
)


def make_result(cmd: str, duration: float, status: str = "success") -> CommandResult:
    return CommandResult(command=cmd, duration=duration, status=status, stdout="", stderr="", returncode=0)


@pytest.fixture
def sample_results():
    # three runs of cmd_a (oldest first) and two runs of cmd_b
    return [
        make_result("cmd_a", 1.0),
        make_result("cmd_b", 2.0),
        make_result("cmd_a", 0.8),
        make_result("cmd_b", 1.8),
        make_result("cmd_a", 0.5),  # most recent
    ]


def test_parse_decay_config_defaults():
    cfg = parse_decay_config({})
    assert cfg.half_life == 3.0
    assert cfg.min_weight == 0.05


def test_parse_decay_config_custom():
    cfg = parse_decay_config({"decay": {"half_life": 5.0, "min_weight": 0.01}})
    assert cfg.half_life == 5.0
    assert cfg.min_weight == 0.01


def test_weight_age_zero_is_one():
    assert _weight(0, 3.0, 0.05) == pytest.approx(1.0)


def test_weight_age_half_life_is_half():
    assert _weight(3, 3.0, 0.05) == pytest.approx(0.5)


def test_weight_respects_min():
    # very old result should be clamped to min_weight
    assert _weight(1000, 3.0, 0.05) == pytest.approx(0.05)


def test_apply_decay_returns_one_entry_per_command(sample_results):
    entries = apply_decay(sample_results)
    commands = {e.command for e in entries}
    assert commands == {"cmd_a", "cmd_b"}


def test_apply_decay_sample_count(sample_results):
    entries = {e.command: e for e in apply_decay(sample_results)}
    assert entries["cmd_a"].sample_count == 3
    assert entries["cmd_b"].sample_count == 2


def test_apply_decay_weighted_mean_favors_recent(sample_results):
    """Weighted mean for cmd_a should be below the raw mean because recent runs are faster."""
    entries = {e.command: e for e in apply_decay(sample_results)}
    e = entries["cmd_a"]
    assert e.weighted_mean < e.raw_mean


def test_apply_decay_speedup_positive_when_recent_faster(sample_results):
    entries = {e.command: e for e in apply_decay(sample_results)}
    assert entries["cmd_a"].speedup_vs_raw > 0


def test_apply_decay_single_run():
    results = [make_result("solo", 1.23)]
    entries = apply_decay(results)
    assert len(entries) == 1
    assert entries[0].weighted_mean == pytest.approx(1.23)
    assert entries[0].raw_mean == pytest.approx(1.23)


def test_entry_to_dict_keys(sample_results):
    e = apply_decay(sample_results)[0]
    d = entry_to_dict(e)
    assert set(d.keys()) == {"command", "weighted_mean", "raw_mean", "sample_count", "speedup_vs_raw", "decay_half_life"}


def test_format_decay_json_valid(sample_results):
    entries = apply_decay(sample_results)
    raw = format_decay_json(entries)
    parsed = json.loads(raw)
    assert len(parsed) == 2


def test_format_decay_table_header(sample_results):
    entries = apply_decay(sample_results)
    table = format_decay_table(entries)
    assert "W.Mean" in table
    assert "Speedup" in table


def test_format_decay_table_empty():
    assert format_decay_table([]) == "No decay data."


def test_decay_summary_counts(sample_results):
    entries = apply_decay(sample_results)
    summary = decay_summary(entries)
    assert "2 commands" in summary
