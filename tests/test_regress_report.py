"""Tests for batchmark.regress_report."""
import json
import pytest
from batchmark.regress import RegressEntry
from batchmark.regress_report import (
    entry_to_dict,
    format_regress_json,
    format_regress_table,
    regress_summary,
)


def make_entry(cmd="echo hi", base=0.10, curr=0.25, regressed=True) -> RegressEntry:
    delta = curr - base
    pct = delta / base * 100 if base else 0.0
    return RegressEntry(
        command=cmd,
        baseline_mean=base,
        current_mean=curr,
        delta=round(delta, 6),
        pct_change=round(pct, 2),
        regressed=regressed,
        reason="150.0% > threshold 10.0%" if regressed else "within threshold",
    )


@pytest.fixture
def entries():
    return [make_entry("echo hi", regressed=True), make_entry("ls", 0.05, 0.06, regressed=False)]


def test_entry_to_dict_keys(entries):
    d = entry_to_dict(entries[0])
    assert set(d.keys()) == {"command", "baseline_mean", "current_mean", "delta", "pct_change", "regressed", "reason"}


def test_entry_to_dict_values(entries):
    d = entry_to_dict(entries[0])
    assert d["command"] == "echo hi"
    assert d["regressed"] is True


def test_format_regress_json_valid(entries):
    output = format_regress_json(entries)
    parsed = json.loads(output)
    assert isinstance(parsed, list)
    assert len(parsed) == 2


def test_format_regress_json_keys(entries):
    parsed = json.loads(format_regress_json(entries))
    assert "regressed" in parsed[0]


def test_format_regress_table_header(entries):
    table = format_regress_table(entries)
    assert "Command" in table
    assert "Pct%" in table


def test_format_regress_table_flags_regressed(entries):
    table = format_regress_table(entries)
    assert "REGR" in table


def test_format_regress_table_empty():
    assert format_regress_table([]) == "No regression data."


def test_regress_summary(entries):
    summary = regress_summary(entries)
    assert "1/2" in summary
    assert "regressed" in summary
