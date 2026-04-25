"""warp_report.py — format WarpedResult lists as JSON or table output."""
from __future__ import annotations

import json
from typing import List

from batchmark.warp import WarpedResult, warp_summary


def warped_to_dict(w: WarpedResult) -> dict:
    return {
        "command": w.command,
        "status": w.status,
        "original_duration": w.original.duration,
        "warped_duration": w.warped_duration,
        "delta": round(w.warped_duration - w.original.duration, 6),
    }


def format_warp_json(warped: List[WarpedResult]) -> str:
    payload = {
        "results": [warped_to_dict(w) for w in warped],
        "summary": warp_summary(warped),
    }
    return json.dumps(payload, indent=2)


def format_warp_table(warped: List[WarpedResult]) -> str:
    if not warped:
        return "No warped results."

    header = f"{'COMMAND':<40} {'STATUS':<10} {'ORIGINAL':>10} {'WARPED':>10} {'DELTA':>10}"
    sep = "-" * len(header)
    rows = [header, sep]
    for w in warped:
        cmd = w.command if len(w.command) <= 38 else w.command[:35] + "..."
        rows.append(
            f"{cmd:<40} {w.status:<10} {w.original.duration:>10.4f} "
            f"{w.warped_duration:>10.4f} {w.warped_duration - w.original.duration:>+10.4f}"
        )
    summary = warp_summary(warped)
    rows.append(sep)
    rows.append(
        f"Total: {summary['count']} results | "
        f"orig={summary['total_original']:.4f}s  "
        f"warped={summary['total_warped']:.4f}s  "
        f"speedup={summary['speedup']}"
    )
    return "\n".join(rows)
