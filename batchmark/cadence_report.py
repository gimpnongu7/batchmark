"""cadence_report.py — format CadenceEntry lists as JSON or table."""
from __future__ import annotations

import json
from typing import List

from batchmark.cadence import CadenceEntry, cadence_summary


def entry_to_dict(entry: CadenceEntry) -> dict:
    return {
        "index": entry.index,
        "command": entry.command,
        "duration": round(entry.duration, 4),
        "gap": round(entry.gap, 4) if entry.gap is not None else None,
        "cumulative": round(entry.cumulative, 4),
        "is_late": entry.is_late,
    }


def format_cadence_json(entries: List[CadenceEntry]) -> str:
    payload = {
        "summary": cadence_summary(entries),
        "cadence": [entry_to_dict(e) for e in entries],
    }
    return json.dumps(payload, indent=2)


def format_cadence_table(entries: List[CadenceEntry]) -> str:
    if not entries:
        return "No cadence data."

    header = f"{'#':>4}  {'Command':<30}  {'Duration':>10}  {'Gap':>8}  {'Cumulative':>12}  Late"
    sep = "-" * len(header)
    rows = [header, sep]

    for e in entries:
        gap_str = f"{e.gap:.4f}" if e.gap is not None else "     --"
        late_str = "*" if e.is_late else " "
        cmd = e.command[:28] + ".." if len(e.command) > 30 else e.command
        rows.append(
            f"{e.index:>4}  {cmd:<30}  {e.duration:>10.4f}  {gap_str:>8}  {e.cumulative:>12.4f}  {late_str}"
        )

    summary = cadence_summary(entries)
    rows.append(sep)
    mean_gap = summary["mean_gap"]
    mg_str = f"{mean_gap:.4f}" if mean_gap is not None else "N/A"
    rows.append(f"Total duration: {summary['total_duration']:.4f}s   Mean gap: {mg_str}s   Commands: {summary['count']}")
    return "\n".join(rows)
