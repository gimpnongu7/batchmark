from __future__ import annotations

import json
from typing import List

from batchmark.fence import FenceResult, fence_summary


def entry_to_dict(fr: FenceResult) -> dict:
    return {
        "command": fr.command,
        "duration": round(fr.duration, 4),
        "status": fr.status,
        "allowed": fr.allowed,
        "reason": fr.reason,
    }


def format_fence_json(fenced: List[FenceResult]) -> str:
    summary = fence_summary(fenced)
    payload = {
        "summary": summary,
        "results": [entry_to_dict(f) for f in fenced],
    }
    return json.dumps(payload, indent=2)


def format_fence_table(fenced: List[FenceResult]) -> str:
    summary = fence_summary(fenced)
    header = f"{'Command':<40} {'Duration':>10} {'Status':<10} {'Allowed':<8} Reason"
    sep = "-" * len(header)
    lines = [header, sep]
    for f in fenced:
        allowed_str = "yes" if f.allowed else "no"
        reason_str = f.reason or ""
        lines.append(
            f"{f.command:<40} {f.duration:>10.3f} {f.status:<10} {allowed_str:<8} {reason_str}"
        )
    lines.append(sep)
    lines.append(
        f"Total: {summary['total']}  Allowed: {summary['allowed']}  Blocked: {summary['blocked']}"
    )
    return "\n".join(lines)
