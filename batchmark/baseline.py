"""Baseline management: save and compare against a reference run."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

from batchmark.runner import CommandResult


@dataclass
class BaselineEntry:
    command: str
    mean_duration: float
    success_rate: float


def _entry_from_results(command: str, results: List[CommandResult]) -> BaselineEntry:
    durations = [r.duration for r in results]
    mean_duration = sum(durations) / len(durations) if durations else 0.0
    successes = sum(1 for r in results if r.returncode == 0)
    success_rate = successes / len(results) if results else 0.0
    return BaselineEntry(command=command, mean_duration=mean_duration, success_rate=success_rate)


def save_baseline(results: List[CommandResult], path: str) -> None:
    """Aggregate results by command and write baseline JSON."""
    grouped: Dict[str, List[CommandResult]] = {}
    for r in results:
        grouped.setdefault(r.command, []).append(r)

    entries = [
        {"command": cmd, "mean_duration": e.mean_duration, "success_rate": e.success_rate}
        for cmd, group in grouped.items()
        for e in [_entry_from_results(cmd, group)]
    ]
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w") as fh:
        json.dump(entries, fh, indent=2)


def load_baseline(path: str) -> Dict[str, BaselineEntry]:
    """Load baseline from JSON file, keyed by command."""
    with open(path) as fh:
        raw = json.load(fh)
    return {
        item["command"]: BaselineEntry(
            command=item["command"],
            mean_duration=item["mean_duration"],
            success_rate=item["success_rate"],
        )
        for item in raw
    }


@dataclass
class BaselineDiff:
    command: str
    baseline_duration: Optional[float]
    current_duration: float
    delta: Optional[float]          # current - baseline
    pct_change: Optional[float]     # percentage change


def compare_to_baseline(
    results: List[CommandResult], baseline: Dict[str, BaselineEntry]
) -> List[BaselineDiff]:
    grouped: Dict[str, List[CommandResult]] = {}
    for r in results:
        grouped.setdefault(r.command, []).append(r)

    diffs = []
    for cmd, group in grouped.items():
        current = _entry_from_results(cmd, group)
        base = baseline.get(cmd)
        if base is not None:
            delta = current.mean_duration - base.mean_duration
            pct = (delta / base.mean_duration * 100) if base.mean_duration else None
        else:
            delta = None
            pct = None
        diffs.append(BaselineDiff(
            command=cmd,
            baseline_duration=base.mean_duration if base else None,
            current_duration=current.mean_duration,
            delta=delta,
            pct_change=pct,
        ))
    return diffs


def format_baseline_table(diffs: List[BaselineDiff]) -> str:
    header = f"{'Command':<40} {'Baseline':>10} {'Current':>10} {'Delta':>10} {'Change':>10}"
    sep = "-" * len(header)
    rows = [header, sep]
    for d in diffs:
        base_s = f"{d.baseline_duration:.3f}s" if d.baseline_duration is not None else "N/A"
        delta_s = f"{d.delta:+.3f}s" if d.delta is not None else "N/A"
        pct_s = f"{d.pct_change:+.1f}%" if d.pct_change is not None else "N/A"
        rows.append(f"{d.command:<40} {base_s:>10} {d.current_duration:>9.3f}s {delta_s:>10} {pct_s:>10}")
    return "\n".join(rows)
