import pytest
from batchmark.runner import CommandResult
from batchmark.dedupe import DedupeConfig, dedupe_results, count_duplicates


def make_result(cmd: str, duration: float = 1.0, exit_code: int = 0) -> CommandResult:
    return CommandResult(
        command=cmd,
        exit_code=exit_code,
        stdout="",
        stderr="",
        duration=duration,
        timed_out=False,
    )


@pytest.fixture
def sample_results():
    return [
        make_result("echo a", 0.5),
        make_result("echo b", 1.0),
        make_result("echo a", 0.3),
        make_result("echo c", 2.0),
        make_result("echo b", 1.5),
    ]


def test_dedupe_first_strategy(sample_results):
    cfg = DedupeConfig(strategy="first")
    result = dedupe_results(sample_results, cfg)
    assert len(result) == 3
    cmds = [r.command for r in result]
    assert cmds == ["echo a", "echo b", "echo c"]
    assert result[0].duration == 0.5  # first echo a
    assert result[1].duration == 1.0  # first echo b


def test_dedupe_last_strategy(sample_results):
    cfg = DedupeConfig(strategy="last")
    result = dedupe_results(sample_results, cfg)
    assert len(result) == 3
    by_cmd = {r.command: r for r in result}
    assert by_cmd["echo a"].duration == 0.3
    assert by_cmd["echo b"].duration == 1.5


def test_dedupe_fastest_strategy(sample_results):
    cfg = DedupeConfig(strategy="fastest")
    result = dedupe_results(sample_results, cfg)
    by_cmd = {r.command: r for r in result}
    assert by_cmd["echo a"].duration == 0.3
    assert by_cmd["echo b"].duration == 1.0


def test_dedupe_slowest_strategy(sample_results):
    cfg = DedupeConfig(strategy="slowest")
    result = dedupe_results(sample_results, cfg)
    by_cmd = {r.command: r for r in result}
    assert by_cmd["echo a"].duration == 0.5
    assert by_cmd["echo b"].duration == 1.5


def test_dedupe_no_duplicates():
    results = [make_result("echo a"), make_result("echo b")]
    out = dedupe_results(results)
    assert len(out) == 2


def test_dedupe_case_insensitive():
    results = [make_result("Echo A", 1.0), make_result("echo a", 0.5)]
    cfg = DedupeConfig(strategy="first", case_sensitive=False)
    out = dedupe_results(results, cfg)
    assert len(out) == 1
    assert out[0].duration == 1.0


def test_dedupe_case_sensitive_keeps_both():
    results = [make_result("Echo A"), make_result("echo a")]
    cfg = DedupeConfig(case_sensitive=True)
    out = dedupe_results(results, cfg)
    assert len(out) == 2


def test_count_duplicates(sample_results):
    dupes = count_duplicates(sample_results)
    assert dupes == {"echo a": 2, "echo b": 2}


def test_count_duplicates_none():
    results = [make_result("echo a"), make_result("echo b")]
    assert count_duplicates(results) == {}
