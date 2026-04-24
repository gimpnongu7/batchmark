"""Formatting helpers for velocity entries."""
from __future__ import annotations

import json
from typing import List, Optional

from batchmark.velocity import VelocityEntry


def entry_to_dict(e: VelocityEntry) -> dict:
    return {
        "index": e.index,
        "command": e.command,
        "duration": round(e.duration, 4),
        "rolling_velocity": round(e.rolling_velocity, 4) if e.rolling_velocity is not None else None,
        "cumulative_velocity": round(e.cumulative_velocity, 4) if e.cumulative_velocity is not None else None,
        "accelerating": e.is_accelerating,
    }


def format_velocity_json(entries: List[VelocityEntry]) -> str:
    return json.dumps([entry_to_dict(e) for e in entries], indent=2)


def format_velocity_table(entries: List[VelocityEntry]) -> str:
    header = f"{'#':>4}  {'Command':<30}  {'Duration':>10}  {'Rolling v/s':>12}  {'Cumul v/s':>10}  {'Accel':>6}"
    sep = "-" * len(header)
    lines = [header, sep]
    for e in entries:
        rv = f"{e.rolling_velocity:.3f}" if e.rolling_velocity is not None else "  -"
        cv = f"{e.cumulative_velocity:.3f}" if e.cumulative_velocity is not None else "  -"
        acc = ""
        if e.is_accelerating is True:
            acc = "up"
        elif e.is_accelerating is False:
            acc = "down"
        lines.append(
            f"{e.index:>4}  {e.command:<30}  {e.duration:>10.4f}  {rv:>12}  {cv:>10}  {acc:>6}"
        )
    return "\n".join(lines)


def velocity_summary(entries: List[VelocityEntry]) -> str:
    last = entries[-1] if entries else None
    if last is None:
        return "No velocity data."
    cv = f"{last.cumulative_velocity:.3f} cmd/s" if last.cumulative_velocity is not None else "n/a"
    rv = f"{last.rolling_velocity:.3f} cmd/s" if last.rolling_velocity is not None else "n/a"
    return f"Final cumulative velocity: {cv}  |  Final rolling velocity: {rv}"
