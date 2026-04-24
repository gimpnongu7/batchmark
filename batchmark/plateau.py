"""Detect when command durations have plateaued (stabilized) across runs."""
from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, stdev
from typing import List, Optional

from batchmark.runner import CommandResult


@dataclass
class PlateauConfig:
    window: int = 5          # number of recent results to examine
    threshold: float = 0.05  # max relative std-dev to consider plateaued
    min_runs: int = 3        # minimum runs before plateau can be declared


@dataclass
class PlateauEntry:
    command: str
    runs: int
    mean_duration: float
    rel_stddev: float
    plateaued: bool
    reason: str


def parse_plateau_config(raw: dict) -> PlateauConfig:
    return PlateauConfig(
        window=int(raw.get("window", 5)),
        threshold=float(raw.get("threshold", 0.05)),
        min_runs=int(raw.get("min_runs", 3)),
    )


def _group_by_command(results: List[CommandResult]) -> dict:
    groups: dict = {}
    for r in results:
        groups.setdefault(r.command, []).append(r)
    return groups


def all_plateaued(entries: List[PlateauEntry]) -> bool:
    """Return True if every entry in the list has plateaued.

    Useful for callers that want a single yes/no answer about whether the
    entire batch of commands has stabilized.
    """
    return bool(entries) and all(e.plateaued for e in entries)


def detect_plateau(
    results: List[CommandResult],
    config: Optional[PlateauConfig] = None,
) -> List[PlateauEntry]:
    if config is None:
        config = PlateauConfig()

    entries: List[PlateauEntry] = []
    groups = _group_by_command(results)

    for command, runs in groups.items():
        n = len(runs)
        window_runs = runs[-config.window :]
        durations = [r.duration for r in window_runs]
        m = mean(durations)

        if n < config.min_runs:
            entries.append(PlateauEntry(
                command=command,
                runs=n,
                mean_duration=m,
                rel_stddev=0.0,
                plateaued=False,
                reason=f"too few runs ({n} < {config.min_runs})",
            ))
            continue

        if len(durations) < 2:
            rel_sd = 0.0
        else:
            sd = stdev(durations)
            rel_sd = (sd / m) if m > 0 else 0.0

        plateaued = rel_sd <= config.threshold
        reason = (
            f"rel_stddev={rel_sd:.4f} <= {config.threshold}"
            if plateaued
            else f"rel_stddev={rel_sd:.4f} > {config.threshold}"
        )

        entries.append(PlateauEntry(
            command=command,
            runs=n,
            mean_duration=m,
            rel_stddev=rel_sd,
            plateaued=plateaued,
            reason=reason,
        ))

    return entries
