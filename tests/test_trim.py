import pytest
from batchmark.runner import CommandResult
from batchmark.trim import TrimConfig, parse_trim_config, trim_results


def make_result(cmd: str, duration: float, status: str = "success") -> CommandResult:
    return CommandResult(command=cmd, duration=duration, status=status, stdout="", stderr="", returncode=0)


@pytest.fixture
def sample_results():
    return [
        make_result("cmd_a", 1.0),
        make_result("cmd_b", 3.0),
        make_result("cmd_c", 2.0),
        make_result("cmd_d", 0.5),
        make_result("cmd_e", 4.0),
    ]


def test_trim_head(sample_results):
    cfg = TrimConfig(head=3)
    out = trim_results(sample_results, cfg)
    assert len(out) == 3
    assert out[0].command == "cmd_a"


def test_trim_tail(sample_results):
    cfg = TrimConfig(tail=2)
    out = trim_results(sample_results, cfg)
    assert len(out) == 2
    assert out[-1].command == "cmd_e"


def test_drop_slowest(sample_results):
    cfg = TrimConfig(drop_slowest=1)
    out = trim_results(sample_results, cfg)
    assert all(r.command != "cmd_e" for r in out)
    assert len(out) == 4


def test_drop_fastest(sample_results):
    cfg = TrimConfig(drop_fastest=1)
    out = trim_results(sample_results, cfg)
    assert all(r.command != "cmd_d" for r in out)
    assert len(out) == 4


def test_drop_both(sample_results):
    cfg = TrimConfig(drop_fastest=1, drop_slowest=1)
    out = trim_results(sample_results, cfg)
    assert len(out) == 3
    assert all(r.command not in ("cmd_d", "cmd_e") for r in out)


def test_drop_all_returns_empty(sample_results):
    cfg = TrimConfig(drop_fastest=3, drop_slowest=3)
    out = trim_results(sample_results, cfg)
    assert out == []


def test_parse_trim_config_defaults():
    cfg = parse_trim_config({})
    assert cfg.head is None
    assert cfg.tail is None
    assert cfg.drop_fastest == 0
    assert cfg.drop_slowest == 0


def test_parse_trim_config_full():
    cfg = parse_trim_config({"head": 5, "drop_fastest": 2, "drop_slowest": 1})
    assert cfg.head == 5
    assert cfg.drop_fastest == 2
    assert cfg.drop_slowest == 1


def test_no_trim_returns_all(sample_results):
    cfg = TrimConfig()
    out = trim_results(sample_results, cfg)
    assert len(out) == len(sample_results)
