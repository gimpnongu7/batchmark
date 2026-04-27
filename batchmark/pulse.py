"""Pulse: track inter-arrival timing between consecutive command results."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from batchmark.runner import CommandResult


@dataclass
class PulseEntry:
    command: str
    duration: float
    status: str
    index: int
    gap: Optional[float]  # seconds since previous result; None for first
    is_burst: bool  # True when gap < burst_threshold

    @property
    def has_gap(self) -> bool:
        return self.gap is not None


@dataclass
class PulseConfig:
    burst_threshold: float = 0.05  # gaps below this are considered bursts
    include_failures: bool = True


def parse_pulse_config(raw: dict) -> PulseConfig:
    return PulseConfig(
        burst_threshold=float(raw.get("burst_threshold", 0.05)),
        include_failures=bool(raw.get("include_failures", True)),
    )


def compute_pulse(
    results: List[CommandResult],
    config: Optional[PulseConfig] = None,
) -> List[PulseEntry]:
    if config is None:
        config = PulseConfig()

    filtered = [
        r for r in results
        if config.include_failures or r.status == "success"
    ]

    entries: List[PulseEntry] = []
    for i, result in enumerate(filtered):
        if i == 0:
            gap = None
            is_burst = False
        else:
            gap = filtered[i].duration - filtered[i - 1].duration
            gap = abs(gap)  # use absolute difference in timing
            is_burst = gap < config.burst_threshold

        entries.append(
            PulseEntry(
                command=result.command,
                duration=result.duration,
                status=result.status,
                index=i,
                gap=gap,
                is_burst=is_burst,
            )
        )

    return entries


def mean_gap(entries: List[PulseEntry]) -> Optional[float]:
    gaps = [e.gap for e in entries if e.gap is not None]
    if not gaps:
        return None
    return sum(gaps) / len(gaps)


def burst_count(entries: List[PulseEntry]) -> int:
    return sum(1 for e in entries if e.is_burst)
