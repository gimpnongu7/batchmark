"""Tests for batchmark.cache."""
import os
import pytest
from batchmark.runner import CommandResult
from batchmark.cache import save_cache, load_cache, clear_cache, _cache_key


def make_result(cmd="echo hi", rc=0, duration=0.1, timed_out=False):
    return CommandResult(
        command=cmd,
        returncode=rc,
        stdout="hi",
        stderr="",
        duration=duration,
        timed_out=timed_out,
    )


@pytest.fixture
def tmp_cache(tmp_path):
    return str(tmp_path / "cache")


def test_cache_key_is_deterministic():
    cmds = ["echo a", "echo b"]
    assert _cache_key(cmds) == _cache_key(cmds)


def test_cache_key_order_independent():
    assert _cache_key(["a", "b"]) == _cache_key(["b", "a"])


def test_save_creates_file(tmp_cache):
    results = [make_result()]
    path = save_cache(["echo hi"], results, cache_dir=tmp_cache)
    assert os.path.exists(path)


def test_load_returns_none_when_missing(tmp_cache):
    result = load_cache(["not cached"], cache_dir=tmp_cache)
    assert result is None


def test_roundtrip(tmp_cache):
    commands = ["echo hello", "ls"]
    results = [make_result("echo hello", duration=0.2), make_result("ls", rc=0, duration=0.05)]
    save_cache(commands, results, cache_dir=tmp_cache)
    loaded = load_cache(commands, cache_dir=tmp_cache)
    assert loaded is not None
    assert len(loaded) == 2
    assert loaded[0].command == "echo hello"
    assert loaded[0].duration == pytest.approx(0.2)
    assert loaded[1].command == "ls"


def test_roundtrip_preserves_timed_out(tmp_cache):
    cmds = ["sleep 10"]
    results = [make_result("sleep 10", rc=-1, timed_out=True)]
    save_cache(cmds, results, cache_dir=tmp_cache)
    loaded = load_cache(cmds, cache_dir=tmp_cache)
    assert loaded[0].timed_out is True


def test_clear_cache_removes_files(tmp_cache):
    save_cache(["echo a"], [make_result()], cache_dir=tmp_cache)
    save_cache(["echo b"], [make_result("echo b")], cache_dir=tmp_cache)
    removed = clear_cache(cache_dir=tmp_cache)
    assert removed == 2
    assert load_cache(["echo a"], cache_dir=tmp_cache) is None


def test_clear_cache_missing_dir_returns_zero(tmp_path):
    count = clear_cache(cache_dir=str(tmp_path / "nonexistent"))
    assert count == 0
