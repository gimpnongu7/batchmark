"""clip_report.py — format clip results for output."""
from __future__ import annotations

import json
from typing import List

from batchmark.runner import CommandResult
from batchmark.clip import ClipConfig, clip_results, clip_summary


def format_clip_json(
    original: List[CommandResult], cfg: ClipConfig
) -> str:
    clipped = clip_results(original, cfg)
    summary = clip_summary(original, clipped)
    payload = {
        "summary": summary,
        "results": [
            {
                "command": r.command,
                "status": r.status,
                "duration": round(r.duration, 6),
                "returncode": r.returncode,
            }
            for r in clipped
        ],
    }
    return json.dumps(payload, indent=2)


def format_clip_table(
    original: List[CommandResult], cfg: ClipConfig
) -> str:
    clipped = clip_results(original, cfg)
    summary = clip_summary(original, clipped)
    lines = [
        f"Clip summary: {summary['clipped_count']} kept, "
        f"{summary['dropped']} dropped (of {summary['original_count']} total)",
        "",
        f"{'Command':<40} {'Status':<10} {'Duration':>10}",
        "-" * 62,
    ]
    for r in clipped:
        lines.append(
            f"{r.command:<40} {r.status:<10} {r.duration:>10.4f}s"
        )
    return "\n".join(lines)
