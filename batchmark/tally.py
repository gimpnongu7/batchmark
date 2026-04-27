from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from batchmark.runner import CommandResult


@dataclass
class TallyEntry:
    command: str
    total: int
    successes: int
    failures: int
    timeouts: int
    success_rate: float
    failure_rate: float


@dataclass
class TallyConfig:
    group_by: str = "command"  # "command" or "status"
    min_runs: int = 1


def parse_tally_config(raw: dict) -> TallyConfig:
    return TallyConfig(
        group_by=raw.get("group_by", "command"),
        min_runs=int(raw.get("min_runs", 1)),
    )


def _safe_rate(count: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round(count / total, 4)


def tally_results(
    results: List[CommandResult],
    config: Optional[TallyConfig] = None,
) -> List[TallyEntry]:
    if config is None:
        config = TallyConfig()

    groups: Dict[str, Dict[str, int]] = {}

    for r in results:
        key = r.command if config.group_by == "command" else r.status
        if key not in groups:
            groups[key] = {"total": 0, "success": 0, "failure": 0, "timeout": 0}
        g = groups[key]
        g["total"] += 1
        if r.status == "success":
            g["success"] += 1
        elif r.status == "timeout":
            g["timeout"] += 1
        else:
            g["failure"] += 1

    entries: List[TallyEntry] = []
    for key, g in groups.items():
        if g["total"] < config.min_runs:
            continue
        entries.append(
            TallyEntry(
                command=key,
                total=g["total"],
                successes=g["success"],
                failures=g["failure"],
                timeouts=g["timeout"],
                success_rate=_safe_rate(g["success"], g["total"]),
                failure_rate=_safe_rate(g["failure"] + g["timeout"], g["total"]),
            )
        )

    return entries


def tally_summary(entries: List[TallyEntry]) -> Dict[str, int]:
    return {
        "groups": len(entries),
        "total_runs": sum(e.total for e in entries),
        "total_successes": sum(e.successes for e in entries),
        "total_failures": sum(e.failures for e in entries),
        "total_timeouts": sum(e.timeouts for e in entries),
    }
