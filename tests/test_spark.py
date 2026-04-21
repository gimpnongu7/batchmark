"""Tests for batchmark.spark sparkline generation."""
import pytest
from batchmark.runner import CommandResult
from batchmark.spark import (
    SparkConfig,
    parse_spark_config,
    sparkline,
    results_sparkline,
    group_sparklines,
    _normalize,
)


def make_result(cmd: str, duration: float, status: str = "success") -> CommandResult:
    return CommandResult(command=cmd, duration=duration, status=status, stdout="", stderr="", returncode=0)


# --- parse_spark_config ---

def test_parse_spark_config_defaults():
    cfg = parse_spark_config({})
    assert cfg.width == 8
    assert cfg.min_val is None
    assert cfg.max_val is None


def test_parse_spark_config_custom():
    cfg = parse_spark_config({"width": 16, "min_val": 0.0, "max_val": 5.0})
    assert cfg.width == 16
    assert cfg.min_val == 0.0
    assert cfg.max_val == 5.0


# --- _normalize ---

def test_normalize_zero_range_returns_half():
    result = _normalize([3.0, 3.0, 3.0], 3.0, 3.0)
    assert all(v == 0.5 for v in result)


def test_normalize_full_range():
    result = _normalize([0.0, 5.0, 10.0], 0.0, 10.0)
    assert result == [0.0, 0.5, 1.0]


# --- sparkline ---

def test_sparkline_empty_returns_empty():
    assert sparkline([]) == ""


def test_sparkline_single_value():
    s = sparkline([1.0])
    assert len(s) == 1


def test_sparkline_length_matches_input():
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    s = sparkline(values)
    assert len(s) == len(values)


def test_sparkline_all_same_values():
    s = sparkline([2.0, 2.0, 2.0])
    # all same → all mid-range chars, no spaces
    assert len(s) == 3
    assert len(set(s)) == 1


def test_sparkline_ascending_chars_non_decreasing():
    values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    s = sparkline(values)
    # each char should be >= previous
    for a, b in zip(s, s[1:]):
        assert ord(a) <= ord(b)


def test_sparkline_with_config_override():
    cfg = SparkConfig(min_val=0.0, max_val=10.0)
    s = sparkline([0.0, 10.0], cfg)
    assert len(s) == 2
    assert s[0] < s[1]


# --- results_sparkline ---

def test_results_sparkline_length():
    results = [make_result(f"cmd{i}", float(i)) for i in range(1, 6)]
    s = results_sparkline(results)
    assert len(s) == 5


def test_results_sparkline_empty():
    assert results_sparkline([]) == ""


# --- group_sparklines ---

def test_group_sparklines_keys():
    groups = {
        "fast": [make_result("a", 0.1), make_result("b", 0.2)],
        "slow": [make_result("c", 2.0), make_result("d", 3.0)],
    }
    out = group_sparklines(groups)
    assert set(out.keys()) == {"fast", "slow"}


def test_group_sparklines_values_are_strings():
    groups = {"g": [make_result("x", 1.0), make_result("y", 2.0)]}
    out = group_sparklines(groups)
    assert isinstance(out["g"], str)
    assert len(out["g"]) == 2
