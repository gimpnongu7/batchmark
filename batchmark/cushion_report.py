"""cushion_report.py — format CushionState diagnostics."""
from __future__ import annotations

import json
from typing import List

from batchmark.cushion import CushionState


def state_to_dict(state: CushionState) -> dict:
    return {
        "enabled": state.config.enabled,
        "base_seconds": state.config.base_seconds,
        "variance_factor": state.config.variance_factor,
        "window": state.config.window,
        "max_seconds": state.config.max_seconds,
        "total_paused": round(state.total_paused, 4),
        "pause_count": state.pause_count,
        "current_cushion": round(state.cushion_seconds(), 4),
    }


def format_cushion_json(state: CushionState) -> str:
    return json.dumps(state_to_dict(state), indent=2)


def format_cushion_table(state: CushionState) -> str:
    d = state_to_dict(state)
    lines: List[str] = [
        "Cushion Summary",
        "-" * 34,
        f"{'Enabled':<22} {str(d['enabled'])}",
        f"{'Base seconds':<22} {d['base_seconds']:.3f}s",
        f"{'Variance factor':<22} {d['variance_factor']}",
        f"{'Window size':<22} {d['window']}",
        f"{'Max seconds':<22} {d['max_seconds']:.3f}s",
        f"{'Current cushion':<22} {d['current_cushion']:.3f}s",
        f"{'Pause count':<22} {d['pause_count']}",
        f"{'Total paused':<22} {d['total_paused']:.3f}s",
    ]
    return "\n".join(lines)
