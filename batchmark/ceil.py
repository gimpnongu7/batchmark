"""ceil.py — round up durations to a configurable resolution boundary."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional

from batchmark.runner import CommandResult


@dataclass
class CeilConfig:
    resolution: float = 0.1   # seconds; round up to nearest multiple
    min_value: Optional[float] = None  # floor applied after ceiling
    max_value: Optional[float] = None  # hard cap applied after ceiling


def parse_ceil_config(raw: dict) -> CeilConfig:
    cfg = raw.get("ceil", {})
    resolution = float(cfg.get("resolution", 0.1))
    if resolution <= 0:
        raise ValueError("ceil.resolution must be positive")
    min_value = cfg.get("min_value")
    max_value = cfg.get("max_value")
    return CeilConfig(
        resolution=resolution,
        min_value=float(min_value) if min_value is not None else None,
        max_value=float(max_value) if max_value is not None else None,
    )


def ceil_duration(duration: float, cfg: CeilConfig) -> float:
    """Round *duration* up to the nearest multiple of cfg.resolution."""
    if cfg.resolution <= 0:
        raise ValueError("resolution must be positive")
    ceiled = math.ceil(duration / cfg.resolution) * cfg.resolution
    # Apply optional bounds
    if cfg.min_value is not None:
        ceiled = max(ceiled, cfg.min_value)
    if cfg.max_value is not None:
        ceiled = min(ceiled, cfg.max_value)
    return round(ceiled, 10)


def ceil_results(results: List[CommandResult], cfg: CeilConfig) -> List[CommandResult]:
    """Return new CommandResult list with durations rounded up."""
    out = []
    for r in results:
        new_duration = ceil_duration(r.duration, cfg)
        out.append(
            CommandResult(
                command=r.command,
                returncode=r.returncode,
                stdout=r.stdout,
                stderr=r.stderr,
                duration=new_duration,
                timed_out=r.timed_out,
            )
        )
    return out


def ceil_summary(original: List[CommandResult], ceiled: List[CommandResult]) -> dict:
    """Return a brief summary comparing original vs ceiled durations."""
    total_original = sum(r.duration for r in original)
    total_ceiled = sum(r.duration for r in ceiled)
    return {
        "count": len(original),
        "total_original": round(total_original, 6),
        "total_ceiled": round(total_ceiled, 6),
        "added": round(total_ceiled - total_original, 6),
    }
