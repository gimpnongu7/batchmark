"""Tests for batchmark.sample."""
import pytest
from batchmark.runner import CommandResult
from batchmark.sample import (
    SampleConfig,
    parse_sample_config,
    sample_results,
)


def make_result(cmd: str, duration: float = 1.0, status: str = "success") -> CommandResult:
    return CommandResult(command=cmd, duration=duration, status=status, stdout="", stderr="", returncode=0)


@pytest.fixture
def sample_results_fixture():
    return [make_result(f"cmd{i}", float(i)) for i in range(10)]


def test_parse_sample_config_defaults():
    cfg = parse_sample_config({})
    assert cfg.strategy == "random"
    assert cfg.n is None
    assert cfg.fraction is None
    assert cfg.seed is None
    assert cfg.nth == 1


def test_parse_sample_config_full():
    cfg = parse_sample_config({"n": 3, "fraction": 0.5, "seed": 42, "strategy": "head", "nth": 2})
    assert cfg.n == 3
    assert cfg.fraction == 0.5
    assert cfg.seed == 42
    assert cfg.strategy == "head"
    assert cfg.nth == 2


def test_sample_head(sample_results_fixture):
    cfg = SampleConfig(n=3, strategy="head")
    out = sample_results(sample_results_fixture, cfg)
    assert len(out) == 3
    assert [r.command for r in out] == ["cmd0", "cmd1", "cmd2"]


def test_sample_tail(sample_results_fixture):
    cfg = SampleConfig(n=3, strategy="tail")
    out = sample_results(sample_results_fixture, cfg)
    assert len(out) == 3
    assert [r.command for r in out] == ["cmd7", "cmd8", "cmd9"]


def test_sample_every_nth(sample_results_fixture):
    cfg = SampleConfig(strategy="every_nth", nth=3)
    out = sample_results(sample_results_fixture, cfg)
    assert [r.command for r in out] == ["cmd0", "cmd3", "cmd6", "cmd9"]


def test_sample_random_reproducible(sample_results_fixture):
    cfg = SampleConfig(n=4, seed=7)
    out1 = sample_results(sample_results_fixture, cfg)
    out2 = sample_results(sample_results_fixture, cfg)
    assert [r.command for r in out1] == [r.command for r in out2]
    assert len(out1) == 4


def test_sample_fraction(sample_results_fixture):
    cfg = SampleConfig(fraction=0.3, seed=1)
    out = sample_results(sample_results_fixture, cfg)
    assert len(out) == 3


def test_sample_empty_list():
    cfg = SampleConfig(n=5)
    assert sample_results([], cfg) == []


def test_sample_n_capped(sample_results_fixture):
    cfg = SampleConfig(n=100, strategy="head")
    out = sample_results(sample_results_fixture, cfg)
    assert len(out) == 10
