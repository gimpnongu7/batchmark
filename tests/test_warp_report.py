"""Tests for batchmark/warp_report.py"""
import json
import pytest
from batchmark.runner import CommandResult
from batchmark.warp import WarpConfig, warp_results
from batchmark.warp_report import warped_to_dict, format_warp_json, format_warp_table


def make_result(cmd="echo hi", duration=1.0, status="success"):
    return CommandResult(command=cmd, duration=duration, status=status,
                         returncode=0, stdout="", stderr="")


@pytest.fixture
def entries():
    results = [
        make_result(cmd="cmd_a", duration=2.0, status="success"),
        make_result(cmd="cmd_b", duration=0.5, status="failure"),
    ]
    return warp_results(results, WarpConfig(factor=2.0))


# --- warped_to_dict ---

def test_warped_to_dict_keys(entries):
    d = warped_to_dict(entries[0])
    assert set(d.keys()) == {"command", "status", "original_duration", "warped_duration", "delta"}


def test_warped_to_dict_values(entries):
    d = warped_to_dict(entries[0])
    assert d["command"] == "cmd_a"
    assert d["original_duration"] == pytest.approx(2.0)
    assert d["warped_duration"] == pytest.approx(4.0)
    assert d["delta"] == pytest.approx(2.0)


def test_warped_to_dict_negative_delta():
    r = make_result(duration=4.0)
    warped = warp_results([r], WarpConfig(factor=0.25))
    d = warped_to_dict(warped[0])
    assert d["delta"] < 0


# --- format_warp_json ---

def test_format_warp_json_valid(entries):
    out = format_warp_json(entries)
    parsed = json.loads(out)
    assert "results" in parsed
    assert "summary" in parsed


def test_format_warp_json_result_count(entries):
    parsed = json.loads(format_warp_json(entries))
    assert len(parsed["results"]) == 2


def test_format_warp_json_summary_keys(entries):
    parsed = json.loads(format_warp_json(entries))
    assert "count" in parsed["summary"]
    assert "speedup" in parsed["summary"]


# --- format_warp_table ---

def test_format_warp_table_header(entries):
    table = format_warp_table(entries)
    assert "COMMAND" in table
    assert "WARPED" in table
    assert "ORIGINAL" in table


def test_format_warp_table_contains_commands(entries):
    table = format_warp_table(entries)
    assert "cmd_a" in table
    assert "cmd_b" in table


def test_format_warp_table_empty():
    assert format_warp_table([]) == "No warped results."


def test_format_warp_table_summary_line(entries):
    table = format_warp_table(entries)
    assert "Total:" in table
    assert "speedup" in table
