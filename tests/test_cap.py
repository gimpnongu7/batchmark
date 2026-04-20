"""Tests for batchmark.cap."""

import pytest

from batchmark.cap import CapConfig, cap_results, cap_summary, parse_cap_config
from batchmark.runner import CommandResult


def make_result(command: str, status: str, duration: float = 1.0) -> CommandResult:
    return CommandResult(
        command=command,
        status=status,
        returncode=0 if status == "success" else 1,
        duration=duration,
        stdout="",
        stderr="",
    )


@pytest.fixture
def sample_results():
    return [
        make_result("cmd_a", "success", 0.1),
        make_result("cmd_b", "success", 0.2),
        make_result("cmd_c", "success", 0.3),
        make_result("cmd_d", "failure", 0.4),
        make_result("cmd_e", "failure", 0.5),
        make_result("cmd_f", "timeout", 1.0),
    ]


def test_parse_cap_config_defaults():
    cfg = parse_cap_config({})
    assert cfg.per_status == {}
    assert cfg.default is None


def test_parse_cap_config_full():
    cfg = parse_cap_config({"per_status": {"success": 2, "failure": 1}, "default": 5})
    assert cfg.per_status == {"success": 2, "failure": 1}
    assert cfg.default == 5


def test_parse_cap_config_invalid_per_status():
    with pytest.raises(ValueError):
        parse_cap_config({"per_status": "bad"})


def test_cap_results_limits_success(sample_results):
    cfg = CapConfig(per_status={"success": 2})
    result = cap_results(sample_results, cfg)
    success_only = [r for r in result if r.status == "success"]
    assert len(success_only) == 2


def test_cap_results_preserves_order(sample_results):
    cfg = CapConfig(per_status={"success": 2})
    result = cap_results(sample_results, cfg)
    commands = [r.command for r in result if r.status == "success"]
    assert commands == ["cmd_a", "cmd_b"]


def test_cap_results_no_limit_passes_through(sample_results):
    cfg = CapConfig(per_status={})
    result = cap_results(sample_results, cfg)
    assert len(result) == len(sample_results)


def test_cap_results_default_applies_to_unknown_status(sample_results):
    cfg = CapConfig(per_status={"success": 10}, default=1)
    result = cap_results(sample_results, cfg)
    failures = [r for r in result if r.status == "failure"]
    timeouts = [r for r in result if r.status == "timeout"]
    assert len(failures) == 1
    assert len(timeouts) == 1


def test_cap_results_zero_cap_drops_all(sample_results):
    cfg = CapConfig(per_status={"failure": 0})
    result = cap_results(sample_results, cfg)
    assert all(r.status != "failure" for r in result)


def test_cap_summary_reports_dropped(sample_results):
    cfg = CapConfig(per_status={"success": 1})
    capped = cap_results(sample_results, cfg)
    dropped = cap_summary(sample_results, capped)
    assert dropped.get("success") == 2


def test_cap_summary_no_dropped_when_under_limit(sample_results):
    cfg = CapConfig(per_status={"success": 10})
    capped = cap_results(sample_results, cfg)
    dropped = cap_summary(sample_results, capped)
    assert "success" not in dropped
