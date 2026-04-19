import pytest
from batchmark.runner import CommandResult
from batchmark.split import (
    SplitRule, SplitConfig, split_results, parse_split_config
)


def make_result(cmd, status="success", duration=0.1):
    return CommandResult(command=cmd, status=status, duration=duration,
                         returncode=0 if status == "success" else 1,
                         stdout="", stderr="")


@pytest.fixture
def sample_results():
    return [
        make_result("echo a", duration=0.01),
        make_result("echo b", duration=0.5),
        make_result("false", status="failure", duration=0.02),
        make_result("sleep 1", status="timeout", duration=1.0),
    ]


def test_split_by_status(sample_results):
    cfg = SplitConfig(rules=[
        SplitRule("failures", lambda r: r.status == "failure"),
        SplitRule("timeouts", lambda r: r.status == "timeout"),
    ])
    sr = split_results(sample_results, cfg)
    assert len(sr.get("failures")) == 1
    assert len(sr.get("timeouts")) == 1
    assert len(sr.get("other")) == 2


def test_split_default_group(sample_results):
    cfg = SplitConfig(rules=[], default_group="ungrouped")
    sr = split_results(sample_results, cfg)
    assert "ungrouped" in sr.group_names()
    assert len(sr.get("ungrouped")) == 4


def test_split_first_rule_wins():
    results = [make_result("cmd", status="failure", duration=2.0)]
    cfg = SplitConfig(rules=[
        SplitRule("failures", lambda r: r.status == "failure"),
        SplitRule("slow", lambda r: r.duration > 1.0),
    ])
    sr = split_results(results, cfg)
    assert len(sr.get("failures")) == 1
    assert len(sr.get("slow")) == 0


def test_parse_split_config_status():
    raw = {"rules": [{"name": "bad", "status": "failure"}]}
    cfg = parse_split_config(raw)
    assert len(cfg.rules) == 1
    assert cfg.rules[0].name == "bad"
    r = make_result("x", status="failure")
    assert cfg.rules[0].predicate(r)


def test_parse_split_config_duration():
    raw = {"rules": [{"name": "slow", "min_duration": 0.3}]}
    cfg = parse_split_config(raw)
    slow = make_result("x", duration=0.5)
    fast = make_result("x", duration=0.1)
    assert cfg.rules[0].predicate(slow)
    assert not cfg.rules[0].predicate(fast)


def test_parse_split_config_contains():
    raw = {"rules": [{"name": "echo", "contains": "echo"}]}
    cfg = parse_split_config(raw)
    assert cfg.rules[0].predicate(make_result("echo hello"))
    assert not cfg.rules[0].predicate(make_result("ls -la"))


def test_parse_split_config_default_group():
    raw = {"default_group": "misc", "rules": []}
    cfg = parse_split_config(raw)
    assert cfg.default_group == "misc"
