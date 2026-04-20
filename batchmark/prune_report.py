"""Formatting helpers for prune results."""
from __future__ import annotations

import json
from typing import List

from batchmark.runner import CommandResult
from batchmark.prune import PruneConfig, prune_summary


def _result_to_dict(r: CommandResult) -> dict:
    return {
        "command": r.command,
        "status": r.status,
        "duration": round(r.duration, 4),
        "stdout": r.stdout,
        "stderr": r.stderr,
    }


def format_prune_json(
    original: List[CommandResult],
    pruned: List[CommandResult],
    config: PruneConfig,
) -> str:
    summary = prune_summary(original, pruned)
    payload = {
        "prune_config": {
            "keep_last": config.keep_last,
            "drop_status": config.drop_status,
            "min_duration": config.min_duration,
            "max_duration": config.max_duration,
        },
        "summary": summary,
        "results": [_result_to_dict(r) for r in pruned],
    }
    return json.dumps(payload, indent=2)


def format_prune_table(
    original: List[CommandResult],
    pruned: List[CommandResult],
) -> str:
    summary = prune_summary(original, pruned)
    lines = [
        f"Pruned {summary['removed_count']} of {summary['original_count']} results "
        f"({summary['pruned_count']} remaining)",
        "",
        f"{'Command':<40} {'Status':<10} {'Duration':>10}",
        "-" * 62,
    ]
    for r in pruned:
        lines.append(f"{r.command:<40} {r.status:<10} {r.duration:>10.4f}")
    return "\n".join(lines)
