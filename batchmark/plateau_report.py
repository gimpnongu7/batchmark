"""Reporting helpers for plateau detection results."""
from __future__ import annotations

import json
from typing import List

from batchmark.plateau import PlateauEntry


def entry_to_dict(entry: PlateauEntry) -> dict:
    return {
        "command": entry.command,
        "runs": entry.runs,
        "mean_duration": round(entry.mean_duration, 4),
        "rel_stddev": round(entry.rel_stddev, 4),
        "plateaued": entry.plateaued,
        "reason": entry.reason,
    }


def format_plateau_json(entries: List[PlateauEntry]) -> str:
    return json.dumps([entry_to_dict(e) for e in entries], indent=2)


def format_plateau_table(entries: List[PlateauEntry]) -> str:
    if not entries:
        return "No plateau data."

    header = f"{'Command':<40} {'Runs':>5} {'Mean(s)':>9} {'RelStdDev':>10} {'Plateaued':>10}"
    sep = "-" * len(header)
    rows = [header, sep]

    for e in entries:
        flag = "YES" if e.plateaued else "no"
        rows.append(
            f"{e.command:<40} {e.runs:>5} {e.mean_duration:>9.4f} "
            f"{e.rel_stddev:>10.4f} {flag:>10}"
        )

    plateaued_count = sum(1 for e in entries if e.plateaued)
    rows.append(sep)
    rows.append(f"Plateaued: {plateaued_count}/{len(entries)} commands")
    return "\n".join(rows)


def plateau_summary(entries: List[PlateauEntry]) -> dict:
    total = len(entries)
    plateaued = sum(1 for e in entries if e.plateaued)
    return {
        "total": total,
        "plateaued": plateaued,
        "not_plateaued": total - plateaued,
    }
