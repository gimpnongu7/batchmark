"""Tests for batchmark.watch"""
import time
from unittest.mock import MagicMock, patch

import pytest

from batchmark.watch import WatchOptions, WatchSummary, _config_mtime, watch
from batchmark.runner import CommandResult


def make_result(cmd="echo hi", status="success", duration=0.1):
    return CommandResult(command=cmd, status=status, duration=duration, stdout="hi", stderr="", returncode=0)


def _fake_config(path):
    return {"commands": ["echo hi"], "timeout": None}


@patch("batchmark.watch._config_mtime")
@patch("batchmark.watch.run_batch")
@patch("batchmark.watch.load_config")
@patch("batchmark.watch.time.sleep")
def test_watch_runs_max_runs(mock_sleep, mock_load, mock_run, mock_mtime):
    mock_mtime.return_value = 1.0
    mock_load.return_value = {"commands": ["echo hi"], "timeout": None}
    mock_run.return_value = [make_result()]

    opts = WatchOptions(config_path="fake.yaml", interval=1.0, max_runs=3)
    summary = watch(opts)

    assert summary.total_runs == 3
    assert len(summary.run_timestamps) == 3


@patch("batchmark.watch._config_mtime")
@patch("batchmark.watch.run_batch")
@patch("batchmark.watch.load_config")
@patch("batchmark.watch.time.sleep")
def test_watch_calls_on_run_callback(mock_sleep, mock_load, mock_run, mock_mtime):
    mock_mtime.return_value = 42.0
    mock_load.return_value = {"commands": ["echo hi"], "timeout": None}
    mock_run.return_value = [make_result()]

    collected = []
    opts = WatchOptions(
        config_path="fake.yaml",
        interval=0.0,
        max_runs=2,
        on_run=lambda n, r: collected.append((n, r)),
    )
    watch(opts)

    assert len(collected) == 2
    assert collected[0][0] == 1
    assert collected[1][0] == 2


@patch("batchmark.watch._config_mtime")
@patch("batchmark.watch.run_batch")
@patch("batchmark.watch.load_config")
@patch("batchmark.watch.time.sleep")
def test_watch_skips_run_when_mtime_unchanged(mock_sleep, mock_load, mock_run, mock_mtime):
    # First call returns new mtime, subsequent calls return same
    mock_mtime.side_effect = [1.0, 1.0, 1.0]
    mock_load.return_value = {"commands": ["echo hi"], "timeout": None}
    mock_run.return_value = [make_result()]

    call_count = 0

    def fake_sleep(t):
        nonlocal call_count
        call_count += 1
        if call_count >= 2:
            # Force exit by exhausting max_runs check via patching
            raise StopIteration

    mock_sleep.side_effect = fake_sleep

    opts = WatchOptions(config_path="fake.yaml", interval=1.0, max_runs=1)
    summary = watch(opts)
    assert summary.total_runs == 1
    mock_run.assert_called_once()


def test_config_mtime_missing_file():
    assert _config_mtime("nonexistent_file_xyz.yaml") == 0.0


def test_watch_summary_record():
    s = WatchSummary()
    s.record()
    s.record()
    assert s.total_runs == 2
    assert len(s.run_timestamps) == 2
