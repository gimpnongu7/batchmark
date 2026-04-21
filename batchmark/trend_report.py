"""Reporting helpers for trend detection results."""
from __future__ import annotations

import json
from typing import List

from batchmark.trend import TrendEntry


def entry_to_dict(entry: TrendEntry) -> dict:
    return {
        "command": entry.command,
        "runs": len(entry.durations),
        "slope": round(entry.slope, 6),
        "direction": entry.direction,
        "first_mean": round(entry.first_mean, 4),
        "last_mean": round(entry.last_mean, 4),
        "pct_change": round(entry.pct_change, 2),
    }


def format_trend_json(entries: List[TrendEntry]) -> str:
    return json.dumps([entry_to_dict(e) for e in entries], indent=2)


def format_trend_table(entries: List[TrendEntry]) -> str:
    if not entries:
        return "No trend data."

    header = f"{'Command':<40} {'Runs':>5} {'Direction':>8} {'Slope':>10} {'% Change':>10}"
    sep = "-" * len(header)
    rows = [header, sep]

    arrows = {"up": "↑", "down": "↓", "stable": "→"}

    for e in entries:
        arrow = arrows.get(e.direction, "?")
        label = f"{arrow} {e.direction}"
        rows.append(
            f"{e.command:<40} {len(e.durations):>5} {label:>8} "
            f"{e.slope:>10.4f} {e.pct_change:>9.1f}%"
        )

    return "\n".join(rows)


def trend_summary(entries: List[TrendEntry]) -> str:
    total = len(entries)
    up = sum(1 for e in entries if e.direction == "up")
    down = sum(1 for e in entries if e.direction == "down")
    stable = sum(1 for e in entries if e.direction == "stable")
    return (
        f"Trend summary: {total} commands — "
        f"{up} slower, {down} faster, {stable} stable"
    )
