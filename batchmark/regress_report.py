"""Formatting helpers for regression detection output."""
from __future__ import annotations

import json
from typing import List

from batchmark.regress import RegressEntry


def entry_to_dict(e: RegressEntry) -> dict:
    return {
        "command": e.command,
        "baseline_mean": e.baseline_mean,
        "current_mean": e.current_mean,
        "delta": e.delta,
        "pct_change": e.pct_change,
        "regressed": e.regressed,
        "reason": e.reason,
    }


def format_regress_json(entries: List[RegressEntry]) -> str:
    return json.dumps([entry_to_dict(e) for e in entries], indent=2)


def format_regress_table(entries: List[RegressEntry]) -> str:
    if not entries:
        return "No regression data."

    header = f"{'Command':<40} {'Base(s)':>8} {'Curr(s)':>8} {'Delta':>8} {'Pct%':>7} {'Flag':<6} Reason"
    sep = "-" * len(header)
    rows = [header, sep]
    for e in entries:
        flag = "REGR" if e.regressed else "ok"
        rows.append(
            f"{e.command:<40} {e.baseline_mean:>8.3f} {e.current_mean:>8.3f}"
            f" {e.delta:>8.3f} {e.pct_change:>6.1f}% {flag:<6} {e.reason}"
        )
    return "\n".join(rows)


def regress_summary(entries: List[RegressEntry]) -> str:
    total = len(entries)
    flagged = sum(1 for e in entries if e.regressed)
    return f"Regression check: {flagged}/{total} command(s) regressed."
