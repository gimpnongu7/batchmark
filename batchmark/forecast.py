"""Forecast future run durations based on historical results."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
import statistics
from batchmark.runner import CommandResult


@dataclass
class ForecastEntry:
    command: str
    sample_count: int
    mean_duration: float
    predicted_next: float
    trend: str  # 'stable', 'improving', 'degrading'


@dataclass
class ForecastConfig:
    window: int = 5          # last N runs to use
    trend_threshold: float = 0.10  # 10% change triggers trend label


def parse_forecast_config(raw: dict) -> ForecastConfig:
    return ForecastConfig(
        window=int(raw.get("window", 5)),
        trend_threshold=float(raw.get("trend_threshold", 0.10)),
    )


def _trend_label(early_mean: float, late_mean: float, threshold: float) -> str:
    if early_mean == 0:
        return "stable"
    delta = (late_mean - early_mean) / early_mean
    if delta > threshold:
        return "degrading"
    if delta < -threshold:
        return "improving"
    return "stable"


def forecast(results: List[CommandResult], cfg: ForecastConfig) -> List[ForecastEntry]:
    """Group results by command and produce a forecast entry for each."""
    grouped: dict[str, List[CommandResult]] = {}
    for r in results:
        grouped.setdefault(r.command, []).append(r)

    entries: List[ForecastEntry] = []
    for cmd, runs in grouped.items():
        durations = [r.duration for r in runs]
        window_durations = durations[-cfg.window:]
        mean = statistics.mean(window_durations)
        predicted = mean

        if len(window_durations) >= 2:
            mid = len(window_durations) // 2
            early = statistics.mean(window_durations[:mid])
            late = statistics.mean(window_durations[mid:])
            trend = _trend_label(early, late, cfg.trend_threshold)
        else:
            trend = "stable"

        entries.append(ForecastEntry(
            command=cmd,
            sample_count=len(window_durations),
            mean_duration=round(mean, 4),
            predicted_next=round(predicted, 4),
            trend=trend,
        ))
    return entries
