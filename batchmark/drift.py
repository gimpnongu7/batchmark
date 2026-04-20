"""Drift detection: compare current run durations against a rolling baseline."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from batchmark.runner import CommandResult


@dataclass
class DriftEntry:
    command: str
    current_duration: float
    baseline_duration: float
    delta: float          # current - baseline
    pct_change: float     # (delta / baseline) * 100, or 0.0 if baseline == 0
    drifted: bool         # True when abs(pct_change) >= threshold


@dataclass
class DriftConfig:
    threshold_pct: float = 20.0   # percent change considered drift
    min_baseline: float = 0.001   # avoid div-by-zero for near-zero baselines


def parse_drift_config(raw: dict) -> DriftConfig:
    return DriftConfig(
        threshold_pct=float(raw.get("threshold_pct", 20.0)),
        min_baseline=float(raw.get("min_baseline", 0.001)),
    )


def _index(results: List[CommandResult]) -> Dict[str, float]:
    """Return mean duration per command from a list of results."""
    totals: Dict[str, float] = {}
    counts: Dict[str, int] = {}
    for r in results:
        totals[r.command] = totals.get(r.command, 0.0) + r.duration
        counts[r.command] = counts.get(r.command, 0) + 1
    return {cmd: totals[cmd] / counts[cmd] for cmd in totals}


def detect_drift(
    current: List[CommandResult],
    baseline: List[CommandResult],
    config: Optional[DriftConfig] = None,
) -> List[DriftEntry]:
    """Compare current results against baseline and flag drifted commands."""
    if config is None:
        config = DriftConfig()

    cur_index = _index(current)
    base_index = _index(baseline)

    entries: List[DriftEntry] = []
    for cmd, cur_dur in cur_index.items():
        base_dur = base_index.get(cmd)
        if base_dur is None:
            continue  # no baseline for this command — skip
        effective_base = max(base_dur, config.min_baseline)
        delta = cur_dur - base_dur
        pct = (delta / effective_base) * 100.0
        entries.append(
            DriftEntry(
                command=cmd,
                current_duration=cur_dur,
                baseline_duration=base_dur,
                delta=delta,
                pct_change=pct,
                drifted=abs(pct) >= config.threshold_pct,
            )
        )
    return sorted(entries, key=lambda e: abs(e.pct_change), reverse=True)
