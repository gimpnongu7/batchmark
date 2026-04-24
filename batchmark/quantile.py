"""Quantile analysis for command durations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from batchmark.runner import CommandResult


@dataclass
class QuantileConfig:
    quantiles: List[float]  # e.g. [0.25, 0.50, 0.75, 0.90, 0.95, 0.99]
    include_failures: bool = False


@dataclass
class QuantileEntry:
    command: str
    quantile: float
    value: float  # duration in seconds at this quantile
    label: str   # e.g. "p50", "p95"


def parse_quantile_config(raw: dict) -> QuantileConfig:
    quantiles = raw.get("quantiles", [0.25, 0.50, 0.75, 0.90, 0.95, 0.99])
    include_failures = raw.get("include_failures", False)
    for q in quantiles:
        if not (0.0 <= q <= 1.0):
            raise ValueError(f"Quantile must be between 0 and 1, got {q}")
    return QuantileConfig(quantiles=quantiles, include_failures=include_failures)


def _quantile_label(q: float) -> str:
    pct = int(round(q * 100))
    return f"p{pct}"


def _interpolate(sorted_vals: List[float], q: float) -> float:
    n = len(sorted_vals)
    if n == 1:
        return sorted_vals[0]
    idx = q * (n - 1)
    lo = int(idx)
    hi = min(lo + 1, n - 1)
    frac = idx - lo
    return sorted_vals[lo] + frac * (sorted_vals[hi] - sorted_vals[lo])


def compute_quantiles(
    results: Sequence[CommandResult],
    config: Optional[QuantileConfig] = None,
) -> List[QuantileEntry]:
    if config is None:
        config = QuantileConfig(quantiles=[0.25, 0.50, 0.75, 0.90, 0.95, 0.99])

    # Group durations by command
    groups: dict[str, List[float]] = {}
    for r in results:
        if not config.include_failures and r.status != "success":
            continue
        groups.setdefault(r.command, []).append(r.duration)

    entries: List[QuantileEntry] = []
    for cmd, durations in groups.items():
        sorted_d = sorted(durations)
        for q in config.quantiles:
            val = _interpolate(sorted_d, q)
            entries.append(QuantileEntry(
                command=cmd,
                quantile=q,
                value=round(val, 6),
                label=_quantile_label(q),
            ))
    return entries
