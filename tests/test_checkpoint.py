"""Tests for batchmark.checkpoint."""
import json
import os
import pytest

from batchmark.runner import CommandResult
from batchmark.checkpoint import (
    save_checkpoint,
    load_checkpoint,
    completed_commands,
    filter_remaining,
    CheckpointConfig,
)


def make_result(cmd, rc=0, duration=0.1, timed_out=False):
    return CommandResult(
        command=cmd,
        returncode=rc,
        stdout="out",
        stderr="",
        duration=duration,
        timed_out=timed_out,
    )


@pytest.fixture
def tmp_cp(tmp_path):
    return str(tmp_path / "checkpoint.json")


def test_save_creates_file(tmp_cp):
    results = [make_result("echo a"), make_result("echo b")]
    save_checkpoint(tmp_cp, results)
    assert os.path.exists(tmp_cp)


def test_save_content(tmp_cp):
    results = [make_result("echo a", duration=0.5)]
    save_checkpoint(tmp_cp, results)
    with open(tmp_cp) as f:
        data = json.load(f)
    assert data[0]["command"] == "echo a"
    assert data[0]["duration"] == pytest.approx(0.5)


def test_load_returns_none_if_missing(tmp_path):
    result = load_checkpoint(str(tmp_path / "nope.json"))
    assert result is None


def test_load_roundtrip(tmp_cp):
    results = [make_result("echo a"), make_result("echo b", rc=1)]
    save_checkpoint(tmp_cp, results)
    loaded = load_checkpoint(tmp_cp)
    assert len(loaded) == 2
    assert loaded[1].returncode == 1
    assert loaded[1].command == "echo b"


def test_completed_commands(tmp_cp):
    results = [make_result("echo a"), make_result("echo b")]
    done = completed_commands(results)
    assert done == {"echo a", "echo b"}


def test_filter_remaining():
    commands = ["echo a", "echo b", "echo c"]
    done = {"echo a"}
    remaining = filter_remaining(commands, done)
    assert remaining == ["echo b", "echo c"]


def test_filter_remaining_all_done():
    commands = ["echo a"]
    remaining = filter_remaining(commands, {"echo a"})
    assert remaining == []


def test_checkpoint_config_defaults():
    cfg = CheckpointConfig(path="/tmp/cp.json")
    assert cfg.resume is True
    assert cfg.auto_save is True
