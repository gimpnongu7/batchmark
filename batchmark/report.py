"""Formatting utilities for benchmark results and stats."""
import json
from typing import List
from batchmark.runner import CommandResult
from batchmark.stats import compute_stats, stats_to_dict


def results_to_dict(results: List[CommandResult]) -> dict:
    entries = [
        {
            "command": r.command,
            "exit_code": r.exit_code,
            "duration": round(r.duration, 4),
            "timed_out": r.timed_out,
        }
        for r in results
    ]
    stats = stats_to_dict(compute_stats(results))
    return {"results": entries, "stats": stats}


def format_json(results: List[CommandResult]) -> str:
    return json.dumps(results_to_dict(results), indent=2)


def format_table(results: List[CommandResult]) -> str:
    header = f"{'COMMAND':<40} {'EXIT':>6} {'DURATION':>10} {'TIMEOUT':>8}"
    separator = "-" * len(header)
    rows = [header, separator]
    for r in results:
        rows.append(
            f"{r.command:<40} {r.exit_code:>6} {r.duration:>10.4f} {str(r.timed_out):>8}"
        )

    stats = compute_stats(results)
    rows.append(separator)
    rows.append(f"Total: {stats.count}  Success: {stats.success_count}  "
                f"Failure: {stats.failure_count}  Timeout: {stats.timeout_count}")
    rows.append(f"Duration — min: {stats.min_duration:.4f}s  "
                f"mean: {stats.mean_duration:.4f}s  "
                f"median: {stats.median_duration:.4f}s  "
                f"p95: {stats.p95_duration:.4f}s  "
                f"max: {stats.max_duration:.4f}s")
    return "\n".join(rows)
