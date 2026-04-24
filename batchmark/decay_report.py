"""Formatting helpers for decay analysis output."""
from __future__ import annotations

import json
from typing import List

from batchmark.decay import DecayEntry


def entry_to_dict(e: DecayEntry) -> dict:
    return {
        "command": e.command,
        "weighted_mean": e.weighted_mean,
        "raw_mean": e.raw_mean,
        "sample_count": e.sample_count,
        "speedup_vs_raw": round(e.speedup_vs_raw, 6),
        "decay_half_life": e.decay_half_life,
    }


def format_decay_json(entries: List[DecayEntry]) -> str:
    return json.dumps([entry_to_dict(e) for e in entries], indent=2)


def format_decay_table(entries: List[DecayEntry]) -> str:
    if not entries:
        return "No decay data."

    header = f"{'Command':<40} {'W.Mean':>10} {'Raw Mean':>10} {'Samples':>8} {'Speedup':>9}"
    sep = "-" * len(header)
    rows = [header, sep]
    for e in entries:
        speedup_pct = f"{e.speedup_vs_raw * 100:+.1f}%"
        rows.append(
            f"{e.command:<40} {e.weighted_mean:>10.4f} {e.raw_mean:>10.4f} "
            f"{e.sample_count:>8} {speedup_pct:>9}"
        )
    return "\n".join(rows)


def decay_summary(entries: List[DecayEntry]) -> str:
    if not entries:
        return "decay: no entries"
    accelerating = sum(1 for e in entries if e.speedup_vs_raw > 0)
    slowing = sum(1 for e in entries if e.speedup_vs_raw < 0)
    return (
        f"decay: {len(entries)} commands — "
        f"{accelerating} getting faster, {slowing} getting slower"
    )
