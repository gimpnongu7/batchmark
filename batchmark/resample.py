"""Resample results by rounding or snapping durations to a fixed resolution."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from batchmark.runner import CommandResult


@dataclass
class ResampleConfig:
    resolution: float = 0.1  # seconds, e.g. 0.1 = round to nearest 100ms
    min_duration: float = 0.0
    max_duration: Optional[float] = None


@dataclass
class ResampledResult:
    original: CommandResult
    resampled_duration: float

    @property
    def command(self) -> str:
        return self.original.command

    @property
    def status(self) -> str:
        return self.original.status


def parse_resample_config(data: dict) -> ResampleConfig:
    """Parse a resample config dict (e.g. from YAML)."""
    return ResampleConfig(
        resolution=float(data.get("resolution", 0.1)),
        min_duration=float(data.get("min_duration", 0.0)),
        max_duration=float(data["max_duration"]) if "max_duration" in data else None,
    )


def _snap(value: float, resolution: float) -> float:
    """Round value to nearest multiple of resolution."""
    if resolution <= 0:
        raise ValueError("resolution must be positive")
    return round(round(value / resolution) * resolution, 10)


def resample_results(
    results: List[CommandResult],
    config: ResampleConfig,
) -> List[ResampledResult]:
    """Return results with durations snapped to the configured resolution."""
    out: List[ResampledResult] = []
    for r in results:
        d = _snap(r.duration, config.resolution)
        d = max(d, config.min_duration)
        if config.max_duration is not None:
            d = min(d, config.max_duration)
        out.append(ResampledResult(original=r, resampled_duration=d))
    return out


def resample_to_dicts(resampled: List[ResampledResult]) -> List[dict]:
    """Convert resampled results to plain dicts for reporting."""
    return [
        {
            "command": r.command,
            "status": r.status,
            "original_duration": r.original.duration,
            "resampled_duration": r.resampled_duration,
        }
        for r in resampled
    ]
