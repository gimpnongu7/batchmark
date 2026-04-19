from dataclasses import dataclass
from typing import List, Optional
from batchmark.runner import CommandResult


@dataclass
class RankedResult:
    rank: int
    result: CommandResult
    score: float

    @property
    def command(self) -> str:
        return self.result.command

    @property
    def duration(self) -> float:
        return self.result.duration

    @property
    def status(self) -> str:
        return self.result.status


def _score(result: CommandResult, by: str) -> float:
    if by == "duration":
        return result.duration
    if by == "exit_code":
        return float(result.exit_code if result.exit_code is not None else 0)
    raise ValueError(f"Unknown ranking key: {by!r}")


def rank_results(
    results: List[CommandResult],
    by: str = "duration",
    ascending: bool = True,
    limit: Optional[int] = None,
) -> List[RankedResult]:
    """Rank results by a numeric field, returning RankedResult list."""
    scored = [(r, _score(r, by)) for r in results]
    scored.sort(key=lambda x: x[1], reverse=not ascending)
    if limit is not None:
        scored = scored[:limit]
    return [
        RankedResult(rank=i + 1, result=r, score=s)
        for i, (r, s) in enumerate(scored)
    ]


def format_rank_table(ranked: List[RankedResult]) -> str:
    """Return a simple text table of ranked results."""
    header = f"{'Rank':<6} {'Command':<40} {'Score':>10} {'Status':<10}"
    sep = "-" * len(header)
    rows = [
        f"{r.rank:<6} {r.command:<40} {r.score:>10.4f} {r.status:<10}"
        for r in ranked
    ]
    return "\n".join([header, sep] + rows)
