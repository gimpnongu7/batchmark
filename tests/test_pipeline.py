import pytest
from unittest.mock import patch
from batchmark.pipeline import (
    PipelineStage, PipelineResult, run_pipeline, parse_pipeline_config
)
from batchmark.runner import CommandResult


def make_result(cmd, exit_code=0, duration=0.1):
    return CommandResult(command=cmd, exit_code=exit_code, duration=duration,
                         stdout="", stderr="", timed_out=False)


def _fake_run_batch(commands, timeout=None):
    return [make_result(c) for c in commands]


def _fake_run_batch_fail(commands, timeout=None):
    return [make_result(c, exit_code=1) for c in commands]


def test_run_pipeline_all_success():
    stages = [PipelineStage("a", ["echo hi"]), PipelineStage("b", ["echo bye"])]
    with patch("batchmark.pipeline.run_batch", side_effect=_fake_run_batch):
        results = run_pipeline(stages)
    assert len(results) == 2
    assert all(not r.skipped for r in results)
    assert all(r.success for r in results)


def test_run_pipeline_stop_on_failure():
    stages = [
        PipelineStage("a", ["fail"], stop_on_failure=True),
        PipelineStage("b", ["echo ok"]),
    ]
    with patch("batchmark.pipeline.run_batch", side_effect=_fake_run_batch_fail):
        results = run_pipeline(stages)
    assert results[0].success is False
    assert results[1].skipped is True


def test_run_pipeline_no_stop_continues():
    stages = [
        PipelineStage("a", ["fail"], stop_on_failure=False),
        PipelineStage("b", ["echo ok"]),
    ]
    call_count = [0]
    def mixed(commands, timeout=None):
        call_count[0] += 1
        if call_count[0] == 1:
            return _fake_run_batch_fail(commands)
        return _fake_run_batch(commands)
    with patch("batchmark.pipeline.run_batch", side_effect=mixed):
        results = run_pipeline(stages)
    assert results[1].skipped is False


def test_on_stage_callback_called():
    stages = [PipelineStage("x", ["echo x"]), PipelineStage("y", ["echo y"])]
    seen = []
    with patch("batchmark.pipeline.run_batch", side_effect=_fake_run_batch):
        run_pipeline(stages, on_stage=lambda pr: seen.append(pr.stage))
    assert seen == ["x", "y"]


def test_parse_pipeline_config():
    raw = {"stages": [
        {"name": "build", "commands": ["make"], "stop_on_failure": True},
        {"name": "test", "commands": ["pytest"], "timeout": 30.0},
    ]}
    stages = parse_pipeline_config(raw)
    assert len(stages) == 2
    assert stages[0].stop_on_failure is True
    assert stages[1].timeout == 30.0


def test_pipeline_result_total_duration():
    pr = PipelineResult(stage="s", results=[
        make_result("a", duration=0.5),
        make_result("b", duration=0.3),
    ])
    assert abs(pr.total_duration - 0.8) < 1e-9
