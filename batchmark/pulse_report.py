"""Reporting utilities for pulse analysis results."""
from __future__ import annotations

import json
from typing import List, Optional

from batchmark.pulse import PulseEntry, mean_gap, burst_count


def entry_to_dict(entry: PulseEntry) -> dict:
    return {
        "index": entry.index,
        "command": entry.command,
        "duration": round(entry.duration, 4),
        "status": entry.status,
        "gap": round(entry.gap, 4) if entry.gap is not None else None,
        "is_burst": entry.is_burst,
    }


def format_pulse_json(entries: List[PulseEntry]) -> str:
    payload = {
        "pulse": [entry_to_dict(e) for e in entries],
        "summary": pulse_summary(entries),
    }
    return json.dumps(payload, indent=2)


def format_pulse_table(entries: List[PulseEntry]) -> str:
    header = f"{'#':<5} {'Command':<30} {'Duration':>10} {'Gap':>10} {'Burst':>6}"
    sep = "-" * len(header)
    rows = [header, sep]
    for e in entries:
        gap_str = f"{e.gap:.4f}" if e.gap is not None else "—"
        burst_str = "yes" if e.is_burst else "no"
        cmd = e.command[:28] + ".." if len(e.command) > 30 else e.command
        rows.append(
            f"{e.index:<5} {cmd:<30} {e.duration:>10.4f} {gap_str:>10} {burst_str:>6}"
        )
    rows.append(sep)
    summary = pulse_summary(entries)
    rows.append(
        f"total={summary['total']}  bursts={summary['burst_count']}  "
        f"mean_gap={summary['mean_gap']}"
    )
    return "\n".join(rows)


def pulse_summary(entries: List[PulseEntry]) -> dict:
    mg = mean_gap(entries)
    return {
        "total": len(entries),
        "burst_count": burst_count(entries),
        "mean_gap": round(mg, 4) if mg is not None else None,
    }
