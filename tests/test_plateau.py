"""Tests for batchmark.plateau and batchmark.plateau_report."""
import json
import pytest

from batchmark.runner import CommandResult
from batchmark.plateau import (
    PlateauConfig,
    detect_plateau,
    parse_plateau_config,
)
from batchmark.plateau_report import (
    entry_to_dict,
    format_plateau_json,
    format_plateau_table,
    plateau_summary,
)


def make_result(command: str, duration: float, status: str = "success") -> CommandResult:
    return CommandResult(command=command, duration=duration, status=status, stdout="", stderr="", returncode=0)


@pytest.fixture
def stable_results():
    # five runs with nearly identical durations
    return [make_result("echo hi", 1.00 + i * 0.001) for i in range(5)]


@pytest.fixture
def unstable_results():
    return [
        make_result("sleep 1", 1.0),
        make_result("sleep 1", 2.5),
        make_result("sleep 1", 0.5),
        make_result("sleep 1", 3.0),
        make_result("sleep 1", 0.2),
    ]


def test_parse_plateau_config_defaults():
    cfg = parse_plateau_config({})
    assert cfg.window == 5
    assert cfg.threshold == 0.05
    assert cfg.min_runs == 3


def test_parse_plateau_config_custom():
    cfg = parse_plateau_config({"window": 3, "threshold": 0.1, "min_runs": 2})
    assert cfg.window == 3
    assert cfg.threshold == 0.1
    assert cfg.min_runs == 2


def test_stable_command_is_plateaued(stable_results):
    entries = detect_plateau(stable_results)
    assert len(entries) == 1
    assert entries[0].plateaued is True


def test_unstable_command_not_plateaued(unstable_results):
    entries = detect_plateau(unstable_results)
    assert len(entries) == 1
    assert entries[0].plateaued is False


def test_too_few_runs_not_plateaued():
    results = [make_result("cmd", 1.0), make_result("cmd", 1.0)]
    cfg = PlateauConfig(min_runs=3)
    entries = detect_plateau(results, cfg)
    assert entries[0].plateaued is False
    assert "too few" in entries[0].reason


def test_multiple_commands_grouped():
    results = [
        *[make_result("a", 1.0 + i * 0.001) for i in range(5)],
        *[make_result("b", 1.0 + i * 1.5) for i in range(5)],
    ]
    entries = detect_plateau(results)
    by_cmd = {e.command: e for e in entries}
    assert by_cmd["a"].plateaued is True
    assert by_cmd["b"].plateaued is False


def test_entry_to_dict_keys(stable_results):
    entries = detect_plateau(stable_results)
    d = entry_to_dict(entries[0])
    assert set(d.keys()) == {"command", "runs", "mean_duration", "rel_stddev", "plateaued", "reason"}


def test_format_plateau_json_valid(stable_results):
    entries = detect_plateau(stable_results)
    out = format_plateau_json(entries)
    parsed = json.loads(out)
    assert isinstance(parsed, list)
    assert parsed[0]["plateaued"] is True


def test_format_plateau_table_header(stable_results):
    entries = detect_plateau(stable_results)
    table = format_plateau_table(entries)
    assert "Command" in table
    assert "Plateaued" in table
    assert "YES" in table


def test_format_plateau_table_empty():
    assert format_plateau_table([]) == "No plateau data."


def test_plateau_summary(stable_results, unstable_results):
    entries = detect_plateau(stable_results + unstable_results)
    summary = plateau_summary(entries)
    assert summary["total"] == 2
    assert summary["plateaued"] == 1
    assert summary["not_plateaued"] == 1
