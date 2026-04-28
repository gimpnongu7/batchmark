from __future__ import annotations

import json
from typing import List

from batchmark.burst import BurstEntry


def entry_to_dict(entry: BurstEntry) -> dict:
    return {
        "command": entry.command,
        "duration": round(entry.duration, 4),
        "status": entry.status,
        "window_count": entry.window_count,
        "throttled": entry.throttled,
        "cooldown_applied": round(entry.cooldown_applied, 4),
    }


def format_burst_json(entries: List[BurstEntry]) -> str:
    return json.dumps([entry_to_dict(e) for e in entries], indent=2)


def format_burst_table(entries: List[BurstEntry]) -> str:
    header = f"{'COMMAND':<30} {'DURATION':>10} {'STATUS':<10} {'WIN_COUNT':>10} {'THROTTLED':<10} {'COOLDOWN':>10}"
    sep = "-" * len(header)
    rows = [header, sep]
    for e in entries:
        rows.append(
            f"{e.command:<30} {e.duration:>10.4f} {e.status:<10} {e.window_count:>10} "
            f"{'yes' if e.throttled else 'no':<10} {e.cooldown_applied:>10.4f}"
        )
    throttled_count = sum(1 for e in entries if e.throttled)
    rows.append(sep)
    rows.append(f"Total: {len(entries)}  Throttled: {throttled_count}")
    return "\n".join(rows)


def burst_summary(entries: List[BurstEntry]) -> dict:
    throttled = [e for e in entries if e.throttled]
    total_cooldown = sum(e.cooldown_applied for e in entries)
    return {
        "total": len(entries),
        "throttled_count": len(throttled),
        "total_cooldown_seconds": round(total_cooldown, 4),
    }
