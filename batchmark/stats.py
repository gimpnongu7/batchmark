"""Statistical aggregation utilities for benchmark results."""
from dataclasses import dataclass
from typing import List
from batchmark.runner import CommandResult


@dataclass
class BatchStats:
    count: int
    success_count: int
    failure_count: int
    timeout_count: int
    min_duration: float
    max_duration: float
    mean_duration: float
    median_duration: float
    p95_duration: float


def compute_stats(results: List[CommandResult]) -> BatchStats:
    """Compute aggregate stats from a list of CommandResult."""
    if not results:
        raise ValueError("Cannot compute stats on empty results list")

    durations = sorted(r.duration for r in results)
    n = len(durations)

    success_count = sum(1 for r in results if r.exit_code == 0)
    timeout_count = sum(1 for r in results if r.timed_out)
    failure_count = n - success_count

    mean = sum(durations) / n
    median = durations[n // 2] if n % 2 != 0 else (durations[n // 2 - 1] + durations[n // 2]) / 2
    p95_idx = min(int(n * 0.95), n - 1)
    p95 = durations[p95_idx]

    return BatchStats(
        count=n,
        success_count=success_count,
        failure_count=failure_count,
        timeout_count=timeout_count,
        min_duration=durations[0],
        max_duration=durations[-1],
        mean_duration=round(mean, 4),
        median_duration=round(median, 4),
        p95_duration=round(p95, 4),
    )


def stats_to_dict(stats: BatchStats) -> dict:
    """Convert a BatchStats instance to a plain dictionary."""
    return {
        "count": stats.count,
        "success_count": stats.success_count,
        "failure_count": stats.failure_count,
        "timeout_count": stats.timeout_count,
        "min_duration": stats.min_duration,
        "max_duration": stats.max_duration,
        "mean_duration": stats.mean_duration,
        "median_duration": stats.median_duration,
        "p95_duration": stats.p95_duration,
    }


def format_stats_summary(stats: BatchStats) -> str:
    """Return a human-readable summary string of the batch stats."""
    success_rate = (stats.success_count / stats.count * 100) if stats.count else 0
    return (
        f"Runs: {stats.count} | "
        f"Success: {stats.success_count} ({success_rate:.1f}%) | "
        f"Failures: {stats.failure_count} | "
        f"Timeouts: {stats.timeout_count} | "
        f"Duration (min/mean/median/p95/max): "
        f"{stats.min_duration:.4f}s / {stats.mean_duration:.4f}s / "
        f"{stats.median_duration:.4f}s / {stats.p95_duration:.4f}s / {stats.max_duration:.4f}s"
    )
