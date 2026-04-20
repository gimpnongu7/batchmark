"""Format replay results for display."""
from __future__ import annotations

import json
from typing import List

from batchmark.replay import ReplayResult


def replay_result_to_dict(rr: ReplayResult) -> dict:
    d = {
        "command": rr.original.command,
        "was_replayed": rr.was_replayed,
        "original_status": rr.original.status,
        "original_duration": round(rr.original.duration, 4),
        "final_status": rr.final.status,
        "final_duration": round(rr.final.duration, 4),
    }
    if rr.was_replayed and rr.replayed is not None:
        d["delta"] = round(rr.final.duration - rr.original.duration, 4)
    else:
        d["delta"] = None
    return d


def format_replay_json(replay_results: List[ReplayResult]) -> str:
    return json.dumps([replay_result_to_dict(r) for r in replay_results], indent=2)


def format_replay_table(replay_results: List[ReplayResult]) -> str:
    header = f"{'Command':<40} {'Replayed':<10} {'Orig Status':<14} {'Final Status':<14} {'Delta':>8}"
    sep = "-" * len(header)
    rows = [header, sep]
    for rr in replay_results:
        d = replay_result_to_dict(rr)
        delta_str = f"{d['delta']:+.4f}" if d["delta"] is not None else "     -"
        rows.append(
            f"{d['command']:<40} {str(d['was_replayed']):<10} {d['original_status']:<14} {d['final_status']:<14} {delta_str:>8}"
        )
    return "\n".join(rows)
