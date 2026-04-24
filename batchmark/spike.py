"""Spike detection: identify commands whose duration exceeds a rolling mean by a threshold."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from batchmark.runner import CommandResult


@dataclass
class SpikeConfig:
    threshold: float = 2.0   # multiplier above rolling mean
    min_samples: int = 3     # minimum results needed before flagging
    window: int = 10         # how many prior results to use for mean


@dataclass
class SpikeEntry:
    result: CommandResult
    rolling_mean: Optional[float]
    is_spike: bool
    ratio: Optional[float]   # result.duration / rolling_mean, or None

    @property
    def command(self) -> str:
        return self.result.command

    @property
    def duration(self) -> float:
        return self.result.duration


def parse_spike_config(raw: dict) -> SpikeConfig:
    return SpikeConfig(
        threshold=float(raw.get("threshold", 2.0)),
        min_samples=int(raw.get("min_samples", 3)),
        window=int(raw.get("window", 10)),
    )


def _mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def detect_spikes(
    results: List[CommandResult],
    config: Optional[SpikeConfig] = None,
) -> List[SpikeEntry]:
    """Return a SpikeEntry for each result, flagging those that exceed the threshold."""
    if config is None:
        config = SpikeConfig()

    entries: List[SpikeEntry] = []
    durations: List[float] = []

    for result in results:
        window_vals = durations[-config.window:] if durations else []

        if len(window_vals) >= config.min_samples:
            rm = _mean(window_vals)
            ratio = result.duration / rm if rm > 0 else None
            is_spike = ratio is not None and ratio >= config.threshold
        else:
            rm = None
            ratio = None
            is_spike = False

        entries.append(SpikeEntry(
            result=result,
            rolling_mean=rm,
            is_spike=is_spike,
            ratio=ratio,
        ))
        durations.append(result.duration)

    return entries
