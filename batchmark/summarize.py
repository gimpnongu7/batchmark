"""summarize.py — produce a human-readable run summary block."""
from dataclasses import dataclass
from typing import List
from batchmark.runner import CommandResult
from batchmark.stats import BatchStats, compute_stats


@dataclass
class RunSummary:
    total: int
    passed: int
    failed: int
    timed_out: int
    fastest_cmd: str
    slowest_cmd: str
    stats: BatchStats


def summarize(results: List[CommandResult]) -> RunSummary:
    if not results:
        raise ValueError("No results to summarize")

    passed = [r for r in results if r.status == "success"]
    failed = [r for r in results if r.status == "failure"]
    timed_out = [r for r in results if r.status == "timeout"]

    # Only consider successful runs for fastest/slowest to avoid skewed results
    completed = [r for r in results if r.status != "timeout"] or results
    sorted_by_dur = sorted(completed, key=lambda r: r.duration)
    fastest = sorted_by_dur[0].command
    slowest = sorted_by_dur[-1].command

    stats = compute_stats(results)

    return RunSummary(
        total=len(results),
        passed=len(passed),
        failed=len(failed),
        timed_out=len(timed_out),
        fastest_cmd=fastest,
        slowest_cmd=slowest,
        stats=stats,
    )


def format_summary(summary: RunSummary) -> str:
    lines = [
        "=== Run Summary ===",
        f"  Total commands : {summary.total}",
        f"  Passed         : {summary.passed}",
        f"  Failed         : {summary.failed}",
        f"  Timed out      : {summary.timed_out}",
        f"  Fastest        : {summary.fastest_cmd}",
        f"  Slowest        : {summary.slowest_cmd}",
        f"  Mean duration  : {summary.stats.mean:.4f}s",
        f"  Median duration: {summary.stats.median:.4f}s",
        f"  Std dev        : {summary.stats.stdev:.4f}s",
    ]
    return "\n".join(lines)
