"""Report helpers for dampened results."""
from __future__ import annotations

import json
from typing import List

from batchmark.dampen import DampenedResult


def entry_to_dict(entry: DampenedResult) -> dict:
    return {
        "command": entry.command,
        "status": entry.status,
        "raw_duration": entry.raw_duration,
        "smoothed_duration": entry.smoothed_duration,
        "alpha": entry.alpha,
        "delta": round(entry.smoothed_duration - entry.raw_duration, 6),
    }


def format_dampen_json(entries: List[DampenedResult]) -> str:
    return json.dumps([entry_to_dict(e) for e in entries], indent=2)


def format_dampen_table(entries: List[DampenedResult]) -> str:
    if not entries:
        return "No dampened results."

    header = f"{'Command':<40} {'Status':<10} {'Raw':>10} {'Smoothed':>10} {'Delta':>10}"
    sep = "-" * len(header)
    rows = [header, sep]
    for e in entries:
        delta = e.smoothed_duration - e.raw_duration
        sign = "+" if delta >= 0 else ""
        rows.append(
            f"{e.command:<40} {e.status:<10} "
            f"{e.raw_duration:>10.4f} {e.smoothed_duration:>10.4f} "
            f"{sign}{delta:>9.4f}"
        )
    return "\n".join(rows)


def dampen_summary(entries: List[DampenedResult]) -> str:
    if not entries:
        return "dampened 0 results"
    total = len(entries)
    reduced = sum(1 for e in entries if e.smoothed_duration < e.raw_duration)
    return f"dampened {total} result(s); {reduced} had duration reduced by smoothing"
