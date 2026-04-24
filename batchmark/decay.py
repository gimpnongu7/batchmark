"""Decay weighting: apply exponential decay to older results so recent runs matter more."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional

from batchmark.runner import CommandResult


@dataclass
class DecayConfig:
    half_life: float = 3.0      # runs; after this many runs weight is halved
    min_weight: float = 0.05    # floor so very old results still count a little


@dataclass
class DecayEntry:
    command: str
    weighted_mean: float
    raw_mean: float
    sample_count: int
    decay_half_life: float

    @property
    def speedup_vs_raw(self) -> float:
        """Positive means recent runs are faster than the unweighted mean."""
        if self.raw_mean == 0:
            return 0.0
        return (self.raw_mean - self.weighted_mean) / self.raw_mean


def parse_decay_config(cfg: dict) -> DecayConfig:
    decay_cfg = cfg.get("decay", {})
    return DecayConfig(
        half_life=float(decay_cfg.get("half_life", 3.0)),
        min_weight=float(decay_cfg.get("min_weight", 0.05)),
    )


def _weight(age: int, half_life: float, min_weight: float) -> float:
    """age=0 is the most recent result."""
    w = math.pow(0.5, age / half_life)
    return max(w, min_weight)


def _index(results: List[CommandResult]) -> dict:
    idx: dict = {}
    for r in results:
        idx.setdefault(r.command, []).append(r)
    return idx


def apply_decay(
    results: List[CommandResult],
    config: Optional[DecayConfig] = None,
) -> List[DecayEntry]:
    """Return one DecayEntry per unique command with exponentially weighted mean duration."""
    if config is None:
        config = DecayConfig()

    entries: List[DecayEntry] = []
    for command, runs in _index(results).items():
        # most-recent last in list; reverse so index 0 = most recent
        ordered = list(reversed(runs))
        weights = [_weight(i, config.half_life, config.min_weight) for i in range(len(ordered))]
        total_w = sum(weights)
        weighted_mean = sum(r.duration * w for r, w in zip(ordered, weights)) / total_w
        raw_mean = sum(r.duration for r in runs) / len(runs)
        entries.append(
            DecayEntry(
                command=command,
                weighted_mean=round(weighted_mean, 6),
                raw_mean=round(raw_mean, 6),
                sample_count=len(runs),
                decay_half_life=config.half_life,
            )
        )
    return entries
