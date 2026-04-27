import pytest
from batchmark.runner import CommandResult
from batchmark.amplify import (
    AmplifyConfig,
    parse_amplify_config,
    amplify_results,
    amplify_summary,
    _should_amplify,
)


def make_result(cmd: str, duration: float, status: str = "success") -> CommandResult:
    return CommandResult(command=cmd, duration=duration, status=status, stdout="", stderr="", returncode=0)


@pytest.fixture
def sample_results():
    return [
        make_result("echo a", 0.5),
        make_result("echo b", 1.5),
        make_result("echo c", 2.0, status="failure"),
        make_result("echo d", 0.1),
    ]


def test_parse_amplify_config_defaults():
    cfg = parse_amplify_config({})
    assert cfg.factor == 1.0
    assert cfg.min_duration is None
    assert cfg.max_duration is None
    assert cfg.only_failures is False


def test_parse_amplify_config_custom():
    cfg = parse_amplify_config({"factor": 2.5, "min_duration": 0.3, "only_failures": True})
    assert cfg.factor == 2.5
    assert cfg.min_duration == 0.3
    assert cfg.only_failures is True


def test_parse_amplify_config_invalid_factor():
    with pytest.raises(ValueError, match="positive"):
        parse_amplify_config({"factor": -1.0})


def test_parse_amplify_config_zero_factor():
    with pytest.raises(ValueError):
        parse_amplify_config({"factor": 0.0})


def test_amplify_results_returns_all(sample_results):
    cfg = AmplifyConfig(factor=2.0)
    entries = amplify_results(sample_results, cfg)
    assert len(entries) == len(sample_results)


def test_amplify_results_scales_duration(sample_results):
    cfg = AmplifyConfig(factor=3.0)
    entries = amplify_results(sample_results, cfg)
    for e in entries:
        assert pytest.approx(e.amplified_duration) == e.original_duration * 3.0
        assert e.was_amplified is True


def test_amplify_min_duration_skips_short(sample_results):
    cfg = AmplifyConfig(factor=10.0, min_duration=1.0)
    entries = amplify_results(sample_results, cfg)
    skipped = [e for e in entries if not e.was_amplified]
    assert all(e.original_duration < 1.0 for e in skipped)


def test_amplify_max_duration_skips_long(sample_results):
    cfg = AmplifyConfig(factor=10.0, max_duration=1.0)
    entries = amplify_results(sample_results, cfg)
    skipped = [e for e in entries if not e.was_amplified]
    assert all(e.original_duration > 1.0 for e in skipped)


def test_amplify_only_failures():
    results = [
        make_result("a", 1.0, status="success"),
        make_result("b", 1.0, status="failure"),
    ]
    cfg = AmplifyConfig(factor=5.0, only_failures=True)
    entries = amplify_results(results, cfg)
    assert entries[0].was_amplified is False
    assert entries[1].was_amplified is True
    assert pytest.approx(entries[1].amplified_duration) == 5.0


def test_amplify_summary_counts(sample_results):
    cfg = AmplifyConfig(factor=2.0, min_duration=1.0)
    entries = amplify_results(sample_results, cfg)
    summary = amplify_summary(entries)
    assert summary["total"] == 4
    assert summary["amplified_count"] + summary["skipped_count"] == 4


def test_amplify_summary_delta():
    results = [make_result("x", 2.0)]
    cfg = AmplifyConfig(factor=3.0)
    entries = amplify_results(results, cfg)
    summary = amplify_summary(entries)
    assert pytest.approx(summary["total_duration_delta"]) == 4.0


def test_amplified_result_properties():
    r = make_result("cmd", 1.0, status="failure")
    cfg = AmplifyConfig(factor=2.0)
    entries = amplify_results([r], cfg)
    e = entries[0]
    assert e.command == "cmd"
    assert e.status == "failure"
