import pytest
from batchmark.timeout import (
    TimeoutConfig,
    resolve_timeout,
    parse_timeout_config,
    budget_remaining,
    effective_timeout,
)


def test_resolve_timeout_uses_default():
    cfg = TimeoutConfig(default=10.0)
    assert resolve_timeout(cfg, "echo hi") == 10.0


def test_resolve_timeout_uses_per_command():
    cfg = TimeoutConfig(default=10.0, per_command={"sleep 5": 3.0})
    assert resolve_timeout(cfg, "sleep 5") == 3.0


def test_resolve_timeout_fallback_for_unknown():
    cfg = TimeoutConfig(default=15.0, per_command={"ls": 2.0})
    assert resolve_timeout(cfg, "pwd") == 15.0


def test_parse_timeout_config_defaults():
    cfg = parse_timeout_config({})
    assert cfg.default == 30.0
    assert cfg.per_command == {}
    assert cfg.global_budget is None


def test_parse_timeout_config_full():
    raw = {
        "timeouts": {
            "default": 20,
            "per_command": {"ls": 5, "sleep 10": 12},
            "global_budget": 60,
        }
    }
    cfg = parse_timeout_config(raw)
    assert cfg.default == 20.0
    assert cfg.per_command == {"ls": 5.0, "sleep 10": 12.0}
    assert cfg.global_budget == 60.0


def test_budget_remaining_no_budget():
    assert budget_remaining(None, 100.0) is None


def test_budget_remaining_within_budget():
    assert budget_remaining(60.0, 20.0) == 40.0


def test_budget_remaining_exhausted():
    assert budget_remaining(60.0, 65.0) == 0.0


def test_effective_timeout_no_budget():
    assert effective_timeout(10.0, None) == 10.0


def test_effective_timeout_clamped_by_budget():
    assert effective_timeout(10.0, 4.0) == 4.0


def test_effective_timeout_not_clamped():
    assert effective_timeout(5.0, 20.0) == 5.0
