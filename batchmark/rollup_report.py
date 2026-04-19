from __future__ import annotations
import json
from typing import List
from batchmark.rollup import RollupGroup
from batchmark.stats import stats_to_dict


def group_to_dict(group: RollupGroup) -> dict:
    return {
        "group": group.name,
        "command_count": group.command_count,
        "success_rate": round(group.success_rate, 4),
        "stats": stats_to_dict(group.stats),
    }


def format_rollup_json(groups: List[RollupGroup]) -> str:
    return json.dumps([group_to_dict(g) for g in groups], indent=2)


def format_rollup_table(groups: List[RollupGroup]) -> str:
    if not groups:
        return "No rollup groups."
    header = f"{'Group':<20} {'Count':>6} {'Success%':>10} {'Mean(s)':>10} {'Min(s)':>8} {'Max(s)':>8}"
    sep = "-" * len(header)
    lines = [header, sep]
    for g in groups:
        s = g.stats
        lines.append(
            f"{g.name:<20} {g.command_count:>6} "
            f"{g.success_rate * 100:>9.1f}% "
            f"{s.mean:>10.4f} "
            f"{s.min:>8.4f} "
            f"{s.max:>8.4f}"
        )
    return "\n".join(lines)
