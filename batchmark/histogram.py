from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from batchmark.runner import CommandResult


@dataclass
class HistogramConfig:
    bins: int = 10
    min_duration: Optional[float] = None
    max_duration: Optional[float] = None
    bar_width: int = 40


@dataclass
class HistogramBin:
    low: float
    high: float
    count: int
    commands: List[str] = field(default_factory=list)

    @property
    def label(self) -> str:
        return f"{self.low:.3f}–{self.high:.3f}s"


def parse_histogram_config(raw: dict) -> HistogramConfig:
    return HistogramConfig(
        bins=int(raw.get("bins", 10)),
        min_duration=raw.get("min_duration"),
        max_duration=raw.get("max_duration"),
        bar_width=int(raw.get("bar_width", 40)),
    )


def build_histogram(
    results: List[CommandResult],
    config: Optional[HistogramConfig] = None,
) -> List[HistogramBin]:
    if config is None:
        config = HistogramConfig()

    durations = [r.duration for r in results]
    if not durations:
        return []

    lo = config.min_duration if config.min_duration is not None else min(durations)
    hi = config.max_duration if config.max_duration is not None else max(durations)

    if hi == lo:
        hi = lo + 1.0

    bin_size = (hi - lo) / config.bins
    bins: List[HistogramBin] = [
        HistogramBin(low=lo + i * bin_size, high=lo + (i + 1) * bin_size, count=0)
        for i in range(config.bins)
    ]

    for r in results:
        if r.duration < lo or r.duration > hi:
            continue
        idx = int((r.duration - lo) / bin_size)
        idx = min(idx, config.bins - 1)
        bins[idx].count += 1
        bins[idx].commands.append(r.command)

    return bins
