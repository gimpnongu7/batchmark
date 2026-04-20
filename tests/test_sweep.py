"""Tests for batchmark.sweep and batchmark.sweep_report."""
import json
import pytest

from batchmark.runner import CommandResult
from batchmark.sweep import (
    SweepConfig,
    SweepResult,
    render_command,
    run_sweep,
    parse_sweep_config,
)
from batchmark.sweep_report import (
    sweep_result_to_dict,
    format_sweep_json,
    format_sweep_table,
)


def make_result(cmd: str, duration: float = 1.0, status: str = "success") -> CommandResult:
    return CommandResult(
        command=cmd,
        returncode=0 if status == "success" else 1,
        stdout="",
        stderr="",
        duration=duration,
        status=status,
    )


# --- render_command ---

def test_render_command_substitutes_value():
    assert render_command("echo {n}", "n", 5) == "echo 5"


def test_render_command_multiple_occurrences():
    assert render_command("sleep {t} && echo {t}", "t", 2) == "sleep 2 && echo 2"


def test_render_command_no_placeholder_unchanged():
    assert render_command("ls -la", "n", 10) == "ls -la"


# --- run_sweep ---

def test_run_sweep_returns_one_per_value():
    cfg = SweepConfig(param_name="n", values=[1, 2, 3], command_template="sleep {n}")
    calls = []

    def fake_run(cmd, timeout):
        calls.append(cmd)
        return make_result(cmd, duration=0.1)

    results = run_sweep(cfg, fake_run)
    assert len(results) == 3
    assert calls == ["sleep 1", "sleep 2", "sleep 3"]


def test_run_sweep_param_values_preserved():
    cfg = SweepConfig(param_name="x", values=["a", "b"], command_template="echo {x}")
    results = run_sweep(cfg, lambda cmd, t: make_result(cmd))
    assert results[0].param_value == "a"
    assert results[1].param_value == "b"


# --- parse_sweep_config ---

def test_parse_sweep_config_basic():
    data = {"param_name": "n", "values": [1, 2], "command_template": "echo {n}"}
    cfg = parse_sweep_config(data)
    assert cfg.param_name == "n"
    assert cfg.values == [1, 2]
    assert cfg.timeout == 30.0


def test_parse_sweep_config_custom_timeout():
    data = {"param_name": "t", "values": [5], "command_template": "sleep {t}", "timeout": 60}
    cfg = parse_sweep_config(data)
    assert cfg.timeout == 60.0


# --- sweep_report ---

def _make_sweep_results():
    return [
        SweepResult(param_value=1, result=make_result("sleep 1", 1.0)),
        SweepResult(param_value=2, result=make_result("sleep 2", 2.0)),
        SweepResult(param_value=3, result=make_result("sleep 3", 0.5, status="failure")),
    ]


def test_sweep_result_to_dict_keys():
    sr = SweepResult(param_value=1, result=make_result("echo 1", 0.5))
    d = sweep_result_to_dict(sr)
    assert set(d.keys()) == {"param_value", "command", "status", "duration", "returncode"}


def test_format_sweep_json_valid():
    data = json.loads(format_sweep_json(_make_sweep_results()))
    assert len(data) == 3
    assert data[0]["param_value"] == 1


def test_format_sweep_table_header():
    table = format_sweep_table(_make_sweep_results())
    assert "PARAM VALUE" in table
    assert "DURATION" in table


def test_format_sweep_table_summary_line():
    table = format_sweep_table(_make_sweep_results())
    assert "3 runs" in table
    assert "2 passed" in table


def test_format_sweep_table_empty():
    assert format_sweep_table([]) == "No sweep results."
