"""Aggregate results from multiple runs into a single summary."""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from batchmark.runner import CommandResult
from batchmark.stats import compute_stats, BatchStats


@dataclass
class AggregateEntry:
    command: str
    runs: int
    stats: BatchStats
    statuses: Dict[str, int] = field(default_factory=dict)


def aggregate_runs(runs: List[List[CommandResult]]) -> List[AggregateEntry]:
    """Combine results from multiple batch runs, grouped by command."""
    grouped: Dict[str, List[CommandResult]] = {}
    for batch in runs:
        for result in batch:
            grouped.setdefault(result.command, []).append(result)

    entries = []
    for command, results in grouped.items():
        stats = compute_stats(results)
        statuses: Dict[str, int] = {}
        for r in results:
            statuses[r.status] = statuses.get(r.status, 0) + 1
        entries.append(AggregateEntry(
            command=command,
            runs=len(results),
            stats=stats,
            statuses=statuses,
        ))
    return entries


def format_aggregate_table(entries: List[AggregateEntry]) -> str:
    """Format aggregated entries as a plain-text table."""
    lines = [
        f"{'Command':<40} {'Runs':>5} {'Mean':>8} {'Min':>8} {'Max':>8} {'OK':>5} {'FAIL':>5}"
    ]
    lines.append("-" * 82)
    for e in entries:
        ok = e.statuses.get("success", 0)
        fail = e.statuses.get("failure", 0)
        lines.append(
            f"{e.command:<40} {e.runs:>5} {e.stats.mean:>8.3f} "
            f"{e.stats.min_duration:>8.3f} {e.stats.max_duration:>8.3f} "
            f"{ok:>5} {fail:>5}"
        )
    return "\n".join(lines)


def aggregate_to_dicts(entries: List[AggregateEntry]) -> List[dict]:
    """Serialize aggregate entries to plain dicts."""
    return [
        {
            "command": e.command,
            "runs": e.runs,
            "statuses": e.statuses,
            "mean": e.stats.mean,
            "min": e.stats.min_duration,
            "max": e.stats.max_duration,
            "median": e.stats.median,
            "stdev": e.stats.stdev,
        }
        for e in entries
    ]
