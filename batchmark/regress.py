"""Regression detection: flag commands whose duration has worsened across runs."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from batchmark.runner import CommandResult


@dataclass
class RegressEntry:
    command: str
    baseline_mean: float
    current_mean: float
    delta: float          # current_mean - baseline_mean
    pct_change: float     # delta / baseline_mean * 100
    regressed: bool
    reason: str


@dataclass
class RegressConfig:
    threshold_pct: float = 10.0   # flag if pct_change exceeds this
    threshold_abs: float = 0.0    # flag if delta exceeds this (0 = disabled)
    min_baseline_runs: int = 1


def parse_regress_config(raw: dict) -> RegressConfig:
    return RegressConfig(
        threshold_pct=float(raw.get("threshold_pct", 10.0)),
        threshold_abs=float(raw.get("threshold_abs", 0.0)),
        min_baseline_runs=int(raw.get("min_baseline_runs", 1)),
    )


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _index(results: Sequence[CommandResult]) -> dict[str, List[float]]:
    idx: dict[str, List[float]] = {}
    for r in results:
        idx.setdefault(r.command, []).append(r.duration)
    return idx


def detect_regressions(
    baseline: Sequence[CommandResult],
    current: Sequence[CommandResult],
    config: Optional[RegressConfig] = None,
) -> List[RegressEntry]:
    if config is None:
        config = RegressConfig()

    base_idx = _index(baseline)
    curr_idx = _index(current)
    entries: List[RegressEntry] = []

    for cmd, curr_durations in curr_idx.items():
        base_durations = base_idx.get(cmd, [])
        if len(base_durations) < config.min_baseline_runs:
            continue

        base_mean = _mean(base_durations)
        curr_mean = _mean(curr_durations)
        delta = curr_mean - base_mean
        pct = (delta / base_mean * 100.0) if base_mean > 0 else 0.0

        regressed = pct > config.threshold_pct or (
            config.threshold_abs > 0 and delta > config.threshold_abs
        )
        reasons = []
        if pct > config.threshold_pct:
            reasons.append(f"{pct:.1f}% > threshold {config.threshold_pct}%")
        if config.threshold_abs > 0 and delta > config.threshold_abs:
            reasons.append(f"delta {delta:.3f}s > abs threshold {config.threshold_abs}s")
        reason = "; ".join(reasons) if reasons else "within threshold"

        entries.append(
            RegressEntry(
                command=cmd,
                baseline_mean=round(base_mean, 6),
                current_mean=round(curr_mean, 6),
                delta=round(delta, 6),
                pct_change=round(pct, 2),
                regressed=regressed,
                reason=reason,
            )
        )

    return entries
