"""Sparkline generation for duration sequences in batchmark reports."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from batchmark.runner import CommandResult

_SPARKS = " ▁▂▃▄▅▆▇█"


@dataclass
class SparkConfig:
    width: int = 8  # number of buckets / chars in sparkline
    min_val: Optional[float] = None  # override auto min
    max_val: Optional[float] = None  # override auto max


def parse_spark_config(raw: dict) -> SparkConfig:
    return SparkConfig(
        width=int(raw.get("width", 8)),
        min_val=raw.get("min_val"),
        max_val=raw.get("max_val"),
    )


def _normalize(values: List[float], lo: float, hi: float) -> List[float]:
    """Scale values to [0, 1]. Returns 0.0 for all if range is zero."""
    span = hi - lo
    if span == 0:
        return [0.5] * len(values)
    return [(v - lo) / span for v in values]


def sparkline(values: List[float], cfg: Optional[SparkConfig] = None) -> str:
    """Return a unicode sparkline string for a list of float values."""
    if not values:
        return ""
    if cfg is None:
        cfg = SparkConfig()

    lo = cfg.min_val if cfg.min_val is not None else min(values)
    hi = cfg.max_val if cfg.max_val is not None else max(values)

    normed = _normalize(values, lo, hi)
    n = len(_SPARKS) - 1  # 8 levels (indices 1-8), index 0 is space
    chars = [_SPARKS[max(1, round(v * n))] for v in normed]
    return "".join(chars)


def results_sparkline(
    results: List[CommandResult],
    cfg: Optional[SparkConfig] = None,
) -> str:
    """Build a sparkline from the durations of a list of CommandResult objects."""
    durations = [r.duration for r in results]
    return sparkline(durations, cfg)


def group_sparklines(
    groups: dict[str, List[CommandResult]],
    cfg: Optional[SparkConfig] = None,
) -> dict[str, str]:
    """Return a dict mapping group name -> sparkline string."""
    return {name: results_sparkline(rs, cfg) for name, rs in groups.items()}
