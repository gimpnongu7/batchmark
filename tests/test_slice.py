import pytest
from batchmark.runner import CommandResult
from batchmark.slice import (
    SliceConfig,
    parse_slice_config,
    slice_results,
    slice_head,
    slice_tail,
    slice_every,
)


def make_result(cmd: str, duration: float, status: str = "success") -> CommandResult:
    return CommandResult(command=cmd, duration=duration, status=status, stdout="", stderr="", returncode=0)


@pytest.fixture
def sample_results():
    return [make_result(f"cmd{i}", float(i)) for i in range(10)]


def test_parse_slice_config_defaults():
    cfg = parse_slice_config({})
    assert cfg.start == 0
    assert cfg.stop is None
    assert cfg.step == 1
    assert cfg.min_time is None
    assert cfg.max_time is None


def test_parse_slice_config_full():
    cfg = parse_slice_config({"start": 2, "stop": 8, "step": 2, "min_time": 1.0, "max_time": 7.0})
    assert cfg.start == 2
    assert cfg.stop == 8
    assert cfg.step == 2


def test_slice_results_basic(sample_results):
    cfg = SliceConfig(start=2, stop=5)
    out = slice_results(sample_results, cfg)
    assert len(out) == 3
    assert out[0].command == "cmd2"


def test_slice_results_step(sample_results):
    cfg = SliceConfig(step=3)
    out = slice_results(sample_results, cfg)
    assert [r.command for r in out] == ["cmd0", "cmd3", "cmd6", "cmd9"]


def test_slice_results_min_time(sample_results):
    cfg = SliceConfig(min_time=5.0)
    out = slice_results(sample_results, cfg)
    assert all(r.duration >= 5.0 for r in out)


def test_slice_results_max_time(sample_results):
    cfg = SliceConfig(max_time=3.0)
    out = slice_results(sample_results, cfg)
    assert all(r.duration <= 3.0 for r in out)


def test_slice_head(sample_results):
    out = slice_head(sample_results, 3)
    assert len(out) == 3
    assert out[-1].command == "cmd2"


def test_slice_tail(sample_results):
    out = slice_tail(sample_results, 3)
    assert len(out) == 3
    assert out[0].command == "cmd7"


def test_slice_tail_zero(sample_results):
    assert slice_tail(sample_results, 0) == []


def test_slice_every(sample_results):
    out = slice_every(sample_results, 2)
    assert [r.command for r in out] == ["cmd0", "cmd2", "cmd4", "cmd6", "cmd8"]


def test_slice_every_invalid(sample_results):
    with pytest.raises(ValueError):
        slice_every(sample_results, 0)
