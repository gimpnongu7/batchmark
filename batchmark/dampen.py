"""Dampen: apply exponential smoothing to reduce noise in repeated command durations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from batchmark.runner import CommandResult


@dataclass
class DampenConfig:
    alpha: float = 0.5          # smoothing factor in (0, 1]
    min_alpha: float = 0.1
    max_alpha: float = 1.0
    field: str = "duration"     # only 'duration' supported for now


@dataclass
class DampenedResult:
    result: CommandResult
    raw_duration: float
    smoothed_duration: float
    alpha: float

    @property
    def command(self) -> str:
        return self.result.command

    @property
    def status(self) -> str:
        return self.result.status


def parse_dampen_config(cfg: dict) -> DampenConfig:
    alpha = float(cfg.get("alpha", 0.5))
    min_alpha = float(cfg.get("min_alpha", 0.1))
    max_alpha = float(cfg.get("max_alpha", 1.0))
    if not (0 < min_alpha <= max_alpha <= 1.0):
        raise ValueError("dampen: require 0 < min_alpha <= max_alpha <= 1.0")
    if not (min_alpha <= alpha <= max_alpha):
        raise ValueError(f"dampen: alpha {alpha} outside [{min_alpha}, {max_alpha}]")
    return DampenConfig(alpha=alpha, min_alpha=min_alpha, max_alpha=max_alpha)


def _ema(values: List[float], alpha: float) -> List[float]:
    """Return exponential moving average for a sequence."""
    if not values:
        return []
    smoothed = [values[0]]
    for v in values[1:]:
        smoothed.append(alpha * v + (1.0 - alpha) * smoothed[-1])
    return smoothed


def dampen_results(
    results: List[CommandResult],
    config: Optional[DampenConfig] = None,
) -> List[DampenedResult]:
    """Apply EMA smoothing to durations, grouped by command."""
    if config is None:
        config = DampenConfig()

    from collections import defaultdict

    groups: dict[str, List[int]] = defaultdict(list)
    for i, r in enumerate(results):
        groups[r.command].append(i)

    dampened: List[Optional[DampenedResult]] = [None] * len(results)

    for cmd, indices in groups.items():
        raw = [results[i].duration for i in indices]
        smoothed = _ema(raw, config.alpha)
        for idx, (orig_idx, s) in enumerate(zip(indices, smoothed)):
            r = results[orig_idx]
            dampened[orig_idx] = DampenedResult(
                result=r,
                raw_duration=r.duration,
                smoothed_duration=round(s, 6),
                alpha=config.alpha,
            )

    return [d for d in dampened if d is not None]  # type: ignore[misc]
