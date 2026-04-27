"""Tests for batchmark.dampen and batchmark.dampen_report."""
from __future__ import annotations

import pytest
from batchmark.runner import CommandResult
from batchmark.dampen import (
    DampenConfig,
    parse_dampen_config,
    dampen_results,
    _ema,
)
from batchmark.dampen_report import (
    entry_to_dict,
    format_dampen_json,
    format_dampen_table,
    dampen_summary,
)


def make_result(cmd: str, duration: float, status: str = "success") -> CommandResult:
    return CommandResult(command=cmd, duration=duration, status=status, stdout="", stderr="", returncode=0)


sample_results = [
    make_result("echo a", 1.0),
    make_result("echo a", 2.0),
    make_result("echo a", 3.0),
    make_result("echo b", 0.5),
    make_result("echo b", 1.5),
]


def test_parse_dampen_config_defaults():
    cfg = parse_dampen_config({})
    assert cfg.alpha == 0.5
    assert cfg.min_alpha == 0.1
    assert cfg.max_alpha == 1.0


def test_parse_dampen_config_custom():
    cfg = parse_dampen_config({"alpha": 0.3, "min_alpha": 0.2, "max_alpha": 0.8})
    assert cfg.alpha == 0.3


def test_parse_dampen_config_invalid_alpha_range():
    with pytest.raises(ValueError, match="alpha"):
        parse_dampen_config({"alpha": 1.5})


def test_parse_dampen_config_invalid_min_max():
    with pytest.raises(ValueError):
        parse_dampen_config({"min_alpha": 0.9, "max_alpha": 0.1})


def test_ema_single_value():
    assert _ema([5.0], 0.5) == [5.0]


def test_ema_two_values():
    result = _ema([1.0, 3.0], 0.5)
    assert result[0] == 1.0
    assert abs(result[1] - 2.0) < 1e-9


def test_ema_alpha_one_returns_raw():
    vals = [1.0, 2.0, 3.0]
    assert _ema(vals, 1.0) == vals


def test_dampen_results_count():
    out = dampen_results(sample_results)
    assert len(out) == len(sample_results)


def test_dampen_results_first_value_unchanged():
    out = dampen_results(sample_results)
    # first occurrence of each command keeps raw value
    echo_a = [e for e in out if e.command == "echo a"]
    assert echo_a[0].smoothed_duration == echo_a[0].raw_duration


def test_dampen_results_smoothed_differs_after_first():
    out = dampen_results(sample_results, DampenConfig(alpha=0.5))
    echo_a = [e for e in out if e.command == "echo a"]
    # second value should be between first and second raw
    assert echo_a[1].smoothed_duration != echo_a[1].raw_duration


def test_entry_to_dict_keys():
    out = dampen_results([make_result("ls", 0.2)])
    d = entry_to_dict(out[0])
    assert set(d.keys()) == {"command", "status", "raw_duration", "smoothed_duration", "alpha", "delta"}


def test_format_dampen_json_valid():
    import json
    out = dampen_results(sample_results)
    text = format_dampen_json(out)
    parsed = json.loads(text)
    assert len(parsed) == len(sample_results)


def test_format_dampen_table_header():
    out = dampen_results(sample_results)
    table = format_dampen_table(out)
    assert "Command" in table
    assert "Smoothed" in table


def test_format_dampen_table_empty():
    assert format_dampen_table([]) == "No dampened results."


def test_dampen_summary_counts():
    out = dampen_results(sample_results)
    summary = dampen_summary(out)
    assert "5" in summary
