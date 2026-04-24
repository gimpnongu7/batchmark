"""Jitter detection: flag results whose duration deviates significantly
from the per-command mean across multiple runs."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from batchmark.runner import CommandResult


@dataclass
class JitterEntry:
    command: str
    duration: float
    mean: float
    deviation: float        # abs(duration - mean)
    deviation_pct: float    # deviation / mean * 100, or 0 if mean == 0
    flagged: bool
    reason: Optional[str]


@dataclass
class JitterConfig:
    threshold_pct: float = 20.0   # flag if deviation_pct > threshold
    min_samples: int = 2          # need at least this many runs per command


def parse_jitter_config(raw: dict) -> JitterConfig:
    return JitterConfig(
        threshold_pct=float(raw.get("threshold_pct", 20.0)),
        min_samples=int(raw.get("min_samples", 2)),
    )


def _mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _index(runs: List[List[CommandResult]]) -> dict:
    """Group durations by command across all runs."""
    groups: dict = {}
    for run in runs:
        for result in run:
            groups.setdefault(result.command, []).append(result.duration)
    return groups


def detect_jitter(
    runs: List[List[CommandResult]],
    config: Optional[JitterConfig] = None,
) -> List[JitterEntry]:
    """Return one JitterEntry per (command, run-result) pair."""
    if config is None:
        config = JitterConfig()

    groups = _index(runs)
    entries: List[JitterEntry] = []

    for run in runs:
        for result in run:
            cmd = result.command
            all_durations = groups.get(cmd, [])
            if len(all_durations) < config.min_samples:
                entries.append(
                    JitterEntry(
                        command=cmd,
                        duration=result.duration,
                        mean=result.duration,
                        deviation=0.0,
                        deviation_pct=0.0,
                        flagged=False,
                        reason="insufficient samples",
                    )
                )
                continue

            mu = _mean(all_durations)
            dev = abs(result.duration - mu)
            pct = (dev / mu * 100.0) if mu > 0 else 0.0
            flagged = pct > config.threshold_pct
            reason = (
                f"deviation {pct:.1f}% exceeds threshold {config.threshold_pct}%"
                if flagged
                else None
            )
            entries.append(
                JitterEntry(
                    command=cmd,
                    duration=result.duration,
                    mean=round(mu, 6),
                    deviation=round(dev, 6),
                    deviation_pct=round(pct, 2),
                    flagged=flagged,
                    reason=reason,
                )
            )

    return entries
