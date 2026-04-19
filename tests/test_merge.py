import pytest
from batchmark.runner import CommandResult
from batchmark.merge import MergeConfig, parse_merge_config, merge_runs, _tag


def make_result(cmd: str, status: str = "success", duration: float = 1.0) -> CommandResult:
    return CommandResult(command=cmd, returncode=0 if status == "success" else 1,
                         stdout="", stderr="", duration=duration,
                         status=status, timed_out=False)


@pytest.fixture
def run_a():
    return [make_result("echo a", duration=0.5), make_result("echo b", duration=1.0)]


@pytest.fixture
def run_b():
    return [make_result("echo b", duration=0.8), make_result("echo c", duration=1.2)]


def test_merge_all_results(run_a, run_b):
    result = merge_runs([run_a, run_b])
    assert len(result) == 4


def test_merge_preserves_order(run_a, run_b):
    result = merge_runs([run_a, run_b])
    assert result[0].command == "echo a"
    assert result[2].command == "echo b"


def test_merge_dedupe_keeps_first(run_a, run_b):
    cfg = MergeConfig(dedupe=True)
    result = merge_runs([run_a, run_b], cfg)
    commands = [r.command for r in result]
    assert commands.count("echo b") == 1
    # first occurrence from run_a has duration 1.0
    b_result = next(r for r in result if r.command == "echo b")
    assert b_result.duration == 1.0


def test_merge_dedupe_total_count(run_a, run_b):
    cfg = MergeConfig(dedupe=True)
    result = merge_runs([run_a, run_b], cfg)
    assert len(result) == 3


def test_merge_tag_source_labels(run_a, run_b):
    cfg = MergeConfig(tag_source=True, sources=["baseline", "current"])
    result = merge_runs([run_a, run_b], cfg)
    assert result[0].command.startswith("[baseline]")
    assert result[2].command.startswith("[current]")


def test_merge_tag_source_fallback_index(run_a, run_b):
    cfg = MergeConfig(tag_source=True)  # no sources list
    result = merge_runs([run_a, run_b], cfg)
    assert result[0].command.startswith("[0]")
    assert result[2].command.startswith("[1]")


def test_parse_merge_config_defaults():
    cfg = parse_merge_config({})
    assert cfg.dedupe is False
    assert cfg.tag_source is False
    assert cfg.sources == []


def test_parse_merge_config_full():
    cfg = parse_merge_config({"dedupe": True, "tag_source": True, "sources": ["a", "b"]})
    assert cfg.dedupe is True
    assert cfg.sources == ["a", "b"]


def test_merge_empty_runs():
    assert merge_runs([]) == []


def test_merge_single_run(run_a):
    result = merge_runs([run_a])
    assert len(result) == 2
