"""Report formatting for smoothed results."""
from __future__ import annotations

import json
from typing import List

from batchmark.smooth import SmoothedResult


def entry_to_dict(sr: SmoothedResult) -> dict:
    return {
        "command": sr.command,
        "status": sr.status,
        "raw_duration": sr.raw_duration,
        "smoothed_duration": sr.smoothed_duration,
        "window_size": sr.window_size,
    }


def format_smooth_json(entries: List[SmoothedResult]) -> str:
    return json.dumps([entry_to_dict(e) for e in entries], indent=2)


def format_smooth_table(entries: List[SmoothedResult]) -> str:
    if not entries:
        return "No smoothed results."

    header = f"{'Command':<40} {'Status':<10} {'Raw (s)':>10} {'Smooth (s)':>12} {'Win':>4}"
    sep = "-" * len(header)
    rows = [header, sep]
    for e in entries:
        cmd = e.command if len(e.command) <= 38 else e.command[:35] + "..."
        rows.append(
            f"{cmd:<40} {e.status:<10} {e.raw_duration:>10.4f} {e.smoothed_duration:>12.4f} {e.window_size:>4}"
        )
    return "\n".join(rows)


def smooth_summary(entries: List[SmoothedResult]) -> str:
    if not entries:
        return "smooth: 0 results"
    total = len(entries)
    avg_raw = sum(e.raw_duration for e in entries) / total
    avg_smooth = sum(e.smoothed_duration for e in entries) / total
    return (
        f"smooth: {total} results | "
        f"avg raw={avg_raw:.4f}s | avg smoothed={avg_smooth:.4f}s | "
        f"window={entries[0].window_size}"
    )
