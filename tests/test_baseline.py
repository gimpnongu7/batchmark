"""Tests for batchmark.baseline module."""
import json
import os
import pytest

from batchmark.baseline import (
    save_baseline,
    load_baseline,
    compare_to_baseline,
    format_baseline_table,
    BaselineEntry,
)
from batchmark.runner import CommandResult


def make_result(command: str, duration: float, returncode: int = 0) -> CommandResult:
    return CommandResult(command=command, returncode=returncode, duration=duration, stdout="", stderr="")


@pytest.fixture
def sample_results():
    return [
        make_result("echo hi", 0.1),
        make_result("echo hi", 0.3),
        make_result("sleep 1", 1.0),
        make_result("sleep 1", 1.2, returncode=1),
    ]


def test_save_creates_file(tmp_path, sample_results):
    path = str(tmp_path / "baseline.json")
    save_baseline(sample_results, path)
    assert os.path.exists(path)


def test_save_content(tmp_path, sample_results):
    path = str(tmp_path / "baseline.json")
    save_baseline(sample_results, path)
    with open(path) as fh:
        data = json.load(fh)
    commands = {entry["command"] for entry in data}
    assert commands == {"echo hi", "sleep 1"}


def test_save_mean_duration(tmp_path, sample_results):
    path = str(tmp_path / "baseline.json")
    save_baseline(sample_results, path)
    with open(path) as fh:
        data = json.load(fh)
    entry = next(e for e in data if e["command"] == "echo hi")
    assert abs(entry["mean_duration"] - 0.2) < 1e-9


def test_save_success_rate(tmp_path, sample_results):
    path = str(tmp_path / "baseline.json")
    save_baseline(sample_results, path)
    with open(path) as fh:
        data = json.load(fh)
    entry = next(e for e in data if e["command"] == "sleep 1")
    assert abs(entry["success_rate"] - 0.5) < 1e-9


def test_load_baseline(tmp_path, sample_results):
    path = str(tmp_path / "baseline.json")
    save_baseline(sample_results, path)
    baseline = load_baseline(path)
    assert "echo hi" in baseline
    assert isinstance(baseline["echo hi"], BaselineEntry)


def test_compare_delta(tmp_path, sample_results):
    path = str(tmp_path / "baseline.json")
    save_baseline(sample_results, path)
    baseline = load_baseline(path)
    new_results = [make_result("echo hi", 0.5), make_result("echo hi", 0.5)]
    diffs = compare_to_baseline(new_results, baseline)
    assert len(diffs) == 1
    diff = diffs[0]
    assert abs(diff.delta - 0.3) < 1e-9


def test_compare_missing_baseline():
    results = [make_result("new cmd", 0.4)]
    diffs = compare_to_baseline(results, {})
    assert diffs[0].baseline_duration is None
    assert diffs[0].delta is None
    assert diffs[0].pct_change is None


def test_format_table_contains_command(tmp_path, sample_results):
    path = str(tmp_path / "baseline.json")
    save_baseline(sample_results, path)
    baseline = load_baseline(path)
    new_results = [make_result("echo hi", 0.4)]
    diffs = compare_to_baseline(new_results, baseline)
    table = format_baseline_table(diffs)
    assert "echo hi" in table
    assert "Current" in table
    assert "Baseline" in table
