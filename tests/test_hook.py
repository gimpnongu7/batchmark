"""Tests for batchmark.hook"""
import pytest
from batchmark.hook import (
    HookConfig,
    HookResult,
    run_hook,
    run_hooks,
    load_hook_config,
)


def test_run_hook_success():
    hr = run_hook("echo hello")
    assert hr.success
    assert hr.returncode == 0
    assert "hello" in hr.stdout


def test_run_hook_failure():
    hr = run_hook("exit 1")
    assert not hr.success
    assert hr.returncode != 0


def test_run_hook_timeout():
    hr = run_hook("sleep 10", timeout=0.1)
    assert not hr.success
    assert hr.returncode == -1
    assert "timeout" in hr.stderr


def test_run_hooks_all_success():
    results = run_hooks(["echo a", "echo b"])
    assert len(results) == 2
    assert all(r.success for r in results)


def test_run_hooks_warn_on_failure():
    # should not raise, just return failed result
    results = run_hooks(["exit 2"], on_failure="warn")
    assert len(results) == 1
    assert not results[0].success


def test_run_hooks_raise_on_failure():
    with pytest.raises(RuntimeError, match="Hook failed"):
        run_hooks(["exit 3"], on_failure="raise")


def test_run_hooks_empty():
    assert run_hooks([]) == []


def test_load_hook_config_full():
    raw = {
        "hooks": {
            "pre_batch": ["echo pre_batch"],
            "post_batch": ["echo post_batch"],
            "pre_command": ["echo pre_cmd"],
            "post_command": ["echo post_cmd"],
        }
    }
    cfg = load_hook_config(raw)
    assert cfg.pre_batch == ["echo pre_batch"]
    assert cfg.post_batch == ["echo post_batch"]
    assert cfg.pre_command == ["echo pre_cmd"]
    assert cfg.post_command == ["echo post_cmd"]


def test_load_hook_config_missing_hooks_key():
    cfg = load_hook_config({})
    assert cfg.pre_batch == []
    assert cfg.post_batch == []


def test_load_hook_config_partial():
    raw = {"hooks": {"pre_batch": ["echo start"]}}
    cfg = load_hook_config(raw)
    assert cfg.pre_batch == ["echo start"]
    assert cfg.post_command == []
