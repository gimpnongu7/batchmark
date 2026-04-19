import pytest
from batchmark.runner import CommandResult
from batchmark.rank import RankedResult, rank_results, format_rank_table


def make_result(cmd: str, duration: float, exit_code: int = 0) -> CommandResult:
    status = "success" if exit_code == 0 else "failure"
    return CommandResult(
        command=cmd,
        duration=duration,
        exit_code=exit_code,
        status=status,
        stdout="",
        stderr="",
    )


@pytest.fixture
def sample_results():
    return [
        make_result("cmd_c", 3.0),
        make_result("cmd_a", 1.0),
        make_result("cmd_b", 2.0),
    ]


def test_rank_ascending(sample_results):
    ranked = rank_results(sample_results, by="duration", ascending=True)
    assert [r.command for r in ranked] == ["cmd_a", "cmd_b", "cmd_c"]


def test_rank_descending(sample_results):
    ranked = rank_results(sample_results, by="duration", ascending=False)
    assert [r.command for r in ranked] == ["cmd_c", "cmd_b", "cmd_a"]


def test_rank_numbers_start_at_one(sample_results):
    ranked = rank_results(sample_results)
    assert ranked[0].rank == 1
    assert ranked[-1].rank == len(sample_results)


def test_rank_limit(sample_results):
    ranked = rank_results(sample_results, limit=2)
    assert len(ranked) == 2


def test_rank_score_matches_duration(sample_results):
    ranked = rank_results(sample_results, by="duration", ascending=True)
    for r in ranked:
        assert r.score == r.duration


def test_rank_unknown_key_raises(sample_results):
    with pytest.raises(ValueError, match="Unknown ranking key"):
        rank_results(sample_results, by="unknown")


def test_format_rank_table_contains_command(sample_results):
    ranked = rank_results(sample_results)
    table = format_rank_table(ranked)
    for r in ranked:
        assert r.command in table


def test_format_rank_table_has_header(sample_results):
    ranked = rank_results(sample_results)
    table = format_rank_table(ranked)
    assert "Rank" in table
    assert "Command" in table
    assert "Score" in table
