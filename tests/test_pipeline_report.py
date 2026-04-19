import json
import pytest
from batchmark.pipeline import PipelineResult
from batchmark.pipeline_report import (
    pipeline_result_to_dict, format_pipeline_json, format_pipeline_table
)
from batchmark.runner import CommandResult


def make_result(cmd, exit_code=0, duration=0.2):
    return CommandResult(command=cmd, exit_code=exit_code, duration=duration,
                         stdout="out", stderr="", timed_out=False)


def make_pr(name, cmds, skipped=False, exit_code=0):
    if skipped:
        return PipelineResult(stage=name, results=[], skipped=True)
    return PipelineResult(stage=name, results=[make_result(c, exit_code=exit_code) for c in cmds])


def test_pipeline_result_to_dict_keys():
    pr = make_pr("build", ["make"])
    d = pipeline_result_to_dict(pr)
    assert set(d.keys()) >= {"stage", "skipped", "success", "total_duration", "commands"}


def test_pipeline_result_to_dict_skipped():
    pr = make_pr("deploy", [], skipped=True)
    d = pipeline_result_to_dict(pr)
    assert d["skipped"] is True
    assert d["commands"] == []


def test_format_pipeline_json_valid():
    prs = [make_pr("a", ["echo 1"]), make_pr("b", ["echo 2"])]
    out = format_pipeline_json(prs)
    data = json.loads(out)
    assert len(data) == 2
    assert data[0]["stage"] == "a"


def test_format_pipeline_table_header():
    prs = [make_pr("stage1", ["ls"])]
    table = format_pipeline_table(prs)
    assert "Stage" in table
    assert "Status" in table
    assert "Duration" in table


def test_format_pipeline_table_skipped_row():
    prs = [make_pr("deploy", [], skipped=True)]
    table = format_pipeline_table(prs)
    assert "SKIPPED" in table


def test_format_pipeline_table_fail_row():
    prs = [make_pr("test", ["pytest"], exit_code=1)]
    table = format_pipeline_table(prs)
    assert "FAIL" in table
