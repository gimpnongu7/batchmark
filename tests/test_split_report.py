import json
import pytest
from batchmark.runner import CommandResult
from batchmark.split import SplitResult
from batchmark.split_report import split_result_to_dicts, format_split_json, format_split_table


def make_result(cmd, status="success", duration=0.1):
    return CommandResult(command=cmd, status=status, duration=duration,
                         returncode=0, stdout="out", stderr="")


@pytest.fixture
def sr():
    return SplitResult(groups={
        "fast": [make_result("echo a", duration=0.01)],
        "slow": [make_result("sleep 1", duration=1.0)],
    })


def test_split_result_to_dicts_keys(sr):
    d = split_result_to_dicts(sr)
    assert set(d.keys()) == {"fast", "slow"}


def test_split_result_to_dicts_values(sr):
    d = split_result_to_dicts(sr)
    assert d["fast"][0]["command"] == "echo a"
    assert d["slow"][0]["duration"] == pytest.approx(1.0)


def test_format_split_json_valid(sr):
    out = format_split_json(sr)
    parsed = json.loads(out)
    assert "fast" in parsed
    assert "slow" in parsed


def test_format_split_table_header(sr):
    out = format_split_table(sr)
    assert "fast" in out
    assert "slow" in out
    assert "COMMAND" in out


def test_format_split_table_row(sr):
    out = format_split_table(sr)
    assert "echo a" in out
    assert "sleep 1" in out
