from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from batchmark.runner import CommandResult


@dataclass
class BiasConfig:
    min_samples: int = 3
    threshold: float = 0.2  # relative skew threshold (0.0 - 1.0)
    direction: str = "both"  # "high", "low", or "both"


@dataclass
class BiasEntry:
    command: str
    mean: float
    median: float
    skew: float  # (mean - median) / mean
    biased: bool
    direction: str  # "high", "low", or "none"
    sample_count: int


def parse_bias_config(raw: dict) -> BiasConfig:
    threshold = float(raw.get("threshold", 0.2))
    if not (0.0 <= threshold <= 1.0):
        raise ValueError(f"threshold must be between 0.0 and 1.0, got {threshold}")
    direction = raw.get("direction", "both")
    if direction not in ("high", "low", "both"):
        raise ValueError(f"direction must be 'high', 'low', or 'both', got {direction!r}")
    return BiasConfig(
        min_samples=int(raw.get("min_samples", 3)),
        threshold=threshold,
        direction=direction,
    )


def _mean(values: List[float]) -> float:
    return sum(values) / len(values)


def _median(values: List[float]) -> float:
    s = sorted(values)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2.0


def _index(results: List[CommandResult]) -> dict:
    groups: dict = {}
    for r in results:
        groups.setdefault(r.command, []).append(r.duration)
    return groups


def detect_bias(
    results: List[CommandResult],
    config: Optional[BiasConfig] = None,
) -> List[BiasEntry]:
    if config is None:
        config = BiasConfig()

    groups = _index(results)
    entries: List[BiasEntry] = []

    for cmd, durations in groups.items():
        if len(durations) < config.min_samples:
            entries.append(
                BiasEntry(
                    command=cmd,
                    mean=_mean(durations),
                    median=_median(durations),
                    skew=0.0,
                    biased=False,
                    direction="none",
                    sample_count=len(durations),
                )
            )
            continue

        m = _mean(durations)
        med = _median(durations)
        skew = (m - med) / m if m != 0.0 else 0.0

        if config.direction == "high":
            biased = skew > config.threshold
        elif config.direction == "low":
            biased = skew < -config.threshold
        else:
            biased = abs(skew) > config.threshold

        if skew > 0:
            direction = "high"
        elif skew < 0:
            direction = "low"
        else:
            direction = "none"

        entries.append(
            BiasEntry(
                command=cmd,
                mean=round(m, 6),
                median=round(med, 6),
                skew=round(skew, 6),
                biased=biased,
                direction=direction,
                sample_count=len(durations),
            )
        )

    return entries
