import pytest
from batchmark.runner import CommandResult
from batchmark.bias import (
    BiasConfig,
    BiasEntry,
    parse_bias_config,
    detect_bias,
)


def make_result(command: str, duration: float, status: str = "success") -> CommandResult:
    return CommandResult(command=command, duration=duration, status=status, stdout="", stderr="", returncode=0)


@pytest.fixture
def skewed_results():
    # mean will be pulled high by the outlier, median stays lower
    return [
        make_result("cmd", 1.0),
        make_result("cmd", 1.0),
        make_result("cmd", 1.0),
        make_result("cmd", 5.0),  # outlier pulls mean up
    ]


@pytest.fixture
def stable_results():
    return [make_result("cmd", float(d)) for d in [1.0, 1.1, 0.9, 1.05, 0.95]]


def test_parse_bias_config_defaults():
    cfg = parse_bias_config({})
    assert cfg.min_samples == 3
    assert cfg.threshold == 0.2
    assert cfg.direction == "both"


def test_parse_bias_config_custom():
    cfg = parse_bias_config({"min_samples": 5, "threshold": 0.1, "direction": "high"})
    assert cfg.min_samples == 5
    assert cfg.threshold == 0.1
    assert cfg.direction == "high"


def test_parse_bias_config_invalid_threshold():
    with pytest.raises(ValueError, match="threshold"):
        parse_bias_config({"threshold": 1.5})


def test_parse_bias_config_invalid_direction():
    with pytest.raises(ValueError, match="direction"):
        parse_bias_config({"direction": "sideways"})


def test_detect_bias_returns_one_entry_per_command(skewed_results):
    entries = detect_bias(skewed_results)
    assert len(entries) == 1


def test_detect_bias_flags_high_skew(skewed_results):
    entries = detect_bias(skewed_results, BiasConfig(threshold=0.1))
    assert entries[0].biased is True
    assert entries[0].direction == "high"


def test_detect_bias_stable_not_flagged(stable_results):
    entries = detect_bias(stable_results, BiasConfig(threshold=0.2))
    assert entries[0].biased is False


def test_detect_bias_direction_low():
    # median pulled high, mean lower — low skew
    results = [
        make_result("cmd", 10.0),
        make_result("cmd", 10.0),
        make_result("cmd", 10.0),
        make_result("cmd", 0.1),  # outlier pulls mean down
    ]
    entries = detect_bias(results, BiasConfig(threshold=0.1, direction="low"))
    assert entries[0].direction == "low"
    assert entries[0].biased is True


def test_detect_bias_direction_high_ignores_low_skew():
    results = [
        make_result("cmd", 10.0),
        make_result("cmd", 10.0),
        make_result("cmd", 10.0),
        make_result("cmd", 0.1),
    ]
    entries = detect_bias(results, BiasConfig(threshold=0.1, direction="high"))
    assert entries[0].biased is False


def test_detect_bias_below_min_samples_not_flagged():
    results = [make_result("cmd", 1.0), make_result("cmd", 9.0)]
    entries = detect_bias(results, BiasConfig(min_samples=3))
    assert entries[0].biased is False


def test_detect_bias_multiple_commands():
    results = [
        make_result("a", 1.0),
        make_result("a", 1.0),
        make_result("a", 5.0),
        make_result("b", 2.0),
        make_result("b", 2.0),
        make_result("b", 2.0),
    ]
    entries = detect_bias(results)
    commands = {e.command for e in entries}
    assert commands == {"a", "b"}


def test_detect_bias_skew_value_is_correct():
    # mean=2.0, median=1.0 => skew = (2-1)/2 = 0.5
    results = [make_result("cmd", d) for d in [1.0, 1.0, 1.0, 5.0]]
    entries = detect_bias(results)
    assert entries[0].skew == pytest.approx(0.375, abs=0.01)
