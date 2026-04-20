"""Formatting helpers for drift detection output."""
from __future__ import annotations

import json
from typing import List

from batchmark.drift import DriftEntry


def entry_to_dict(e: DriftEntry) -> dict:
    return {
        "command": e.command,
        "current_duration": round(e.current_duration, 4),
        "baseline_duration": round(e.baseline_duration, 4),
        "delta": round(e.delta, 4),
        "pct_change": round(e.pct_change, 2),
        "drifted": e.drifted,
    }


def format_drift_json(entries: List[DriftEntry]) -> str:
    return json.dumps([entry_to_dict(e) for e in entries], indent=2)


def format_drift_table(entries: List[DriftEntry]) -> str:
    if not entries:
        return "No drift data."

    header = f"{'Command':<40} {'Current':>10} {'Baseline':>10} {'Delta':>10} {'Pct%':>8} {'Drift?':>7}"
    sep = "-" * len(header)
    rows = [header, sep]
    for e in entries:
        flag = "YES" if e.drifted else "no"
        rows.append(
            f"{e.command:<40} {e.current_duration:>10.4f} {e.baseline_duration:>10.4f}"
            f" {e.delta:>+10.4f} {e.pct_change:>+8.2f} {flag:>7}"
        )
    drifted_count = sum(1 for e in entries if e.drifted)
    rows.append(sep)
    rows.append(f"Drifted: {drifted_count}/{len(entries)} commands")
    return "\n".join(rows)
