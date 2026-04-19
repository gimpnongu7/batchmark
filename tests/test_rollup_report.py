import json
import pytest
from batchmark.runner import CommandResult
from batchmark.rollup import rollup, RollupConfig
from batchmark.rollup_report import group_to_dict, format_rollup_json, format_rollup_table


def make_result(cmd, status="success", duration=1.0):
    return CommandResult(command=cmd, status=status, duration=duration,
                         stdout="", stderr="", returncode=0)


@pytest.fixture
def groups():
    results = [
        make_result("cmd:a", "success", 1.0),
        make_result("cmd:b", "success", 3.0),
        make_result("cmd:c", "failure", 0.5),
    ]
    return rollup(results, RollupConfig(group_by="status"))


def test_group_to_dict_keys(groups):
    d = group_to_dict(groups[0])
    assert "group" in d
    assert "command_count" in d
    assert "success_rate" in d
    assert "stats" in d


def test_group_to_dict_values(groups):
    by_name = {g.name: g for g in groups}
    d = group_to_dict(by_name["success"])
    assert d["command_count"] == 2
    assert d["success_rate"] == 1.0


def test_format_rollup_json_valid(groups):
    out = format_rollup_json(groups)
    parsed = json.loads(out)
    assert isinstance(parsed, list)
    assert len(parsed) == 2


def test_format_rollup_table_header(groups):
    out = format_rollup_table(groups)
    assert "Group" in out
    assert "Count" in out
    assert "Success%" in out


def test_format_rollup_table_rows(groups):
    out = format_rollup_table(groups)
    assert "success" in out
    assert "failure" in out


def test_format_rollup_table_empty():
    out = format_rollup_table([])
    assert "No rollup groups" in out
