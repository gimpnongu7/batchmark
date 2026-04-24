"""Reporting helpers for stagger execution metadata."""
from __future__ import annotations

import json
from typing import List

from batchmark.runner import CommandResult


def stagger_summary(results: List[CommandResult], total_stagger_time: float) -> dict:
    """Return a summary dict describing stagger overhead."""
    return {
        "command_count": len(results),
        "total_stagger_time_s": round(total_stagger_time, 4),
        "mean_stagger_time_s": (
            round(total_stagger_time / len(results), 4) if results else 0.0
        ),
    }


def result_to_dict(result: CommandResult, index: int, delay: float) -> dict:
    return {
        "index": index,
        "command": result.command,
        "status": result.status,
        "duration": round(result.duration, 4),
        "stagger_delay": round(delay, 4),
    }


def format_stagger_json(
    results: List[CommandResult],
    delays: List[float],
    total_stagger_time: float,
) -> str:
    rows = [
        result_to_dict(r, i, d) for i, (r, d) in enumerate(zip(results, delays))
    ]
    payload = {
        "summary": stagger_summary(results, total_stagger_time),
        "results": rows,
    }
    return json.dumps(payload, indent=2)


def format_stagger_table(
    results: List[CommandResult],
    delays: List[float],
) -> str:
    header = f"{'#':<4}  {'command':<30}  {'status':<8}  {'duration':>10}  {'delay':>8}"
    sep = "-" * len(header)
    lines = [header, sep]
    for i, (r, d) in enumerate(zip(results, delays)):
        cmd = r.command[:28] + ".." if len(r.command) > 30 else r.command
        lines.append(
            f"{i:<4}  {cmd:<30}  {r.status:<8}  {r.duration:>10.4f}  {d:>8.4f}"
        )
    return "\n".join(lines)
