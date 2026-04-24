"""Velocity tracking: measure throughput (commands/sec) across runs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from batchmark.runner import CommandResult


@dataclass
class VelocityConfig:
    window: int = 10          # rolling window size for smoothing
    min_samples: int = 2      # minimum results needed to compute velocity


@dataclass
class VelocityEntry:
    index: int                # position in the result list (0-based)
    command: str
    duration: float
    rolling_velocity: Optional[float]   # commands/sec over window, or None
    cumulative_velocity: Optional[float]  # commands/sec over all so far

    @property
    def is_accelerating(self) -> Optional[bool]:
        """True if rolling > cumulative (speeding up)."""
        if self.rolling_velocity is None or self.cumulative_velocity is None:
            return None
        return self.rolling_velocity > self.cumulative_velocity


def parse_velocity_config(raw: dict) -> VelocityConfig:
    return VelocityConfig(
        window=int(raw.get("window", 10)),
        min_samples=int(raw.get("min_samples", 2)),
    )


def _mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def compute_velocity(
    results: List[CommandResult],
    config: Optional[VelocityConfig] = None,
) -> List[VelocityEntry]:
    if config is None:
        config = VelocityConfig()

    entries: List[VelocityEntry] = []
    durations: List[float] = []

    for i, r in enumerate(results):
        durations.append(r.duration)
        n = i + 1

        # cumulative velocity: n commands / total elapsed
        total_time = sum(durations)
        cumulative = (n / total_time) if total_time > 0 and n >= config.min_samples else None

        # rolling velocity over last `window` items
        window_slice = durations[max(0, n - config.window):n]
        if len(window_slice) >= config.min_samples:
            window_time = sum(window_slice)
            rolling = (len(window_slice) / window_time) if window_time > 0 else None
        else:
            rolling = None

        entries.append(VelocityEntry(
            index=i,
            command=r.command,
            duration=r.duration,
            rolling_velocity=rolling,
            cumulative_velocity=cumulative,
        ))

    return entries
