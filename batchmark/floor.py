"""floor.py — round durations down to the nearest resolution boundary."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional

from batchmark.runner import CommandResult


@dataclass
class FloorConfig:
    resolution: float = 0.1   # seconds; must be > 0
    min_duration: Optional[float] = None  # hard floor after rounding


def parse_floor_config(raw: dict) -> FloorConfig:
    resolution = float(raw.get("resolution", 0.1))
    if resolution <= 0:
        raise ValueError(f"floor resolution must be > 0, got {resolution}")
    min_duration = raw.get("min_duration")
    return FloorConfig(
        resolution=resolution,
        min_duration=float(min_duration) if min_duration is not None else None,
    )


def floor_duration(duration: float, cfg: FloorConfig) -> float:
    """Round *duration* down to the nearest *cfg.resolution* boundary."""
    floored = math.floor(duration / cfg.resolution) * cfg.resolution
    # keep a sensible number of decimal places to avoid floating-point noise
    floored = round(floored, 10)
    if cfg.min_duration is not None:
        floored = max(floored, cfg.min_duration)
    return floored


def floor_results(
    results: List[CommandResult], cfg: FloorConfig
) -> List[CommandResult]:
    """Return new CommandResult list with durations floored."""
    out = []
    for r in results:
        floored = floor_duration(r.duration, cfg)
        out.append(
            CommandResult(
                command=r.command,
                returncode=r.returncode,
                stdout=r.stdout,
                stderr=r.stderr,
                duration=floored,
                timed_out=r.timed_out,
            )
        )
    return out


def floor_summary(original: List[CommandResult], floored: List[CommandResult]) -> dict:
    """Return a summary dict comparing original vs floored durations."""
    deltas = [o.duration - f.duration for o, f in zip(original, floored)]
    return {
        "count": len(original),
        "total_shaved": round(sum(deltas), 10),
        "max_shaved": round(max(deltas), 10) if deltas else 0.0,
        "min_shaved": round(min(deltas), 10) if deltas else 0.0,
    }
