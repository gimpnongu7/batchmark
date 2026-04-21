"""Trend detection across multiple runs of the same commands."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from batchmark.runner import CommandResult


@dataclass
class TrendEntry:
    command: str
    durations: List[float]
    slope: float          # seconds per run (positive = getting slower)
    direction: str        # "up", "down", "stable"
    first_mean: float
    last_mean: float
    pct_change: float     # (last_mean - first_mean) / first_mean * 100


@dataclass
class TrendConfig:
    window: int = 3          # runs per half when comparing first vs last
    stable_threshold: float = 0.05  # 5% change considered stable


def parse_trend_config(raw: dict) -> TrendConfig:
    return TrendConfig(
        window=int(raw.get("window", 3)),
        stable_threshold=float(raw.get("stable_threshold", 0.05)),
    )


def _mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _slope(values: List[float]) -> float:
    """Simple linear regression slope over index."""
    n = len(values)
    if n < 2:
        return 0.0
    xs = list(range(n))
    x_mean = _mean(xs)
    y_mean = _mean(values)
    num = sum((xs[i] - x_mean) * (values[i] - y_mean) for i in range(n))
    den = sum((xs[i] - x_mean) ** 2 for i in range(n))
    return num / den if den != 0 else 0.0


def detect_trends(
    runs: List[List[CommandResult]],
    config: Optional[TrendConfig] = None,
) -> List[TrendEntry]:
    """Detect per-command duration trends across multiple runs."""
    if config is None:
        config = TrendConfig()

    # collect durations per command in run order
    by_command: dict[str, List[float]] = {}
    for run in runs:
        for r in run:
            by_command.setdefault(r.command, []).append(r.duration)

    entries: List[TrendEntry] = []
    for cmd, durations in by_command.items():
        slope = _slope(durations)
        w = min(config.window, max(1, len(durations) // 2))
        first_mean = _mean(durations[:w])
        last_mean = _mean(durations[-w:])
        if first_mean == 0:
            pct = 0.0
        else:
            pct = (last_mean - first_mean) / first_mean * 100.0

        if abs(pct) / 100.0 <= config.stable_threshold:
            direction = "stable"
        elif pct > 0:
            direction = "up"
        else:
            direction = "down"

        entries.append(TrendEntry(
            command=cmd,
            durations=durations,
            slope=slope,
            direction=direction,
            first_mean=first_mean,
            last_mean=last_mean,
            pct_change=pct,
        ))

    return entries
