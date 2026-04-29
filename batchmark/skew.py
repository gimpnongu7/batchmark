"""Skew detection: measures asymmetry in duration distributions per command."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from batchmark.runner import CommandResult


@dataclass
class SkewEntry:
    command: str
    run_count: int
    mean: float
    median: float
    skew: float          # (mean - median) / stddev, or 0 if stddev == 0
    direction: str       # "right", "left", or "symmetric"
    flagged: bool
    reason: Optional[str]


@dataclass
class SkewConfig:
    threshold: float = 0.2   # absolute skew value above which a result is flagged
    min_runs: int = 3        # minimum samples needed to compute skew


def parse_skew_config(raw: dict) -> SkewConfig:
    threshold = float(raw.get("threshold", 0.2))
    min_runs = int(raw.get("min_runs", 3))
    if threshold < 0:
        raise ValueError("threshold must be >= 0")
    if min_runs < 2:
        raise ValueError("min_runs must be >= 2")
    return SkewConfig(threshold=threshold, min_runs=min_runs)


def _mean(values: List[float]) -> float:
    return sum(values) / len(values)


def _median(values: List[float]) -> float:
    s = sorted(values)
    n = len(s)
    mid = n // 2
    return (s[mid - 1] + s[mid]) / 2.0 if n % 2 == 0 else s[mid]


def _stddev(values: List[float], mean: float) -> float:
    if len(values) < 2:
        return 0.0
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return variance ** 0.5


def _group_by_command(results: List[CommandResult]) -> dict:
    groups: dict = {}
    for r in results:
        groups.setdefault(r.command, []).append(r)
    return groups


def detect_skew(
    results: List[CommandResult],
    config: Optional[SkewConfig] = None,
) -> List[SkewEntry]:
    if config is None:
        config = SkewConfig()

    groups = _group_by_command(results)
    entries: List[SkewEntry] = []

    for cmd, runs in groups.items():
        durations = [r.duration for r in runs]
        n = len(durations)

        if n < config.min_runs:
            entries.append(SkewEntry(
                command=cmd,
                run_count=n,
                mean=_mean(durations),
                median=_median(durations),
                skew=0.0,
                direction="symmetric",
                flagged=False,
                reason=f"too few runs ({n} < {config.min_runs})",
            ))
            continue

        mu = _mean(durations)
        med = _median(durations)
        sd = _stddev(durations, mu)
        skew = (mu - med) / sd if sd > 0 else 0.0

        if skew > 0:
            direction = "right"
        elif skew < 0:
            direction = "left"
        else:
            direction = "symmetric"

        flagged = abs(skew) >= config.threshold
        reason = (
            f"skew={skew:.3f} exceeds threshold {config.threshold}" if flagged else None
        )

        entries.append(SkewEntry(
            command=cmd,
            run_count=n,
            mean=round(mu, 6),
            median=round(med, 6),
            skew=round(skew, 6),
            direction=direction,
            flagged=flagged,
            reason=reason,
        ))

    return entries
