"""Reporting utilities for forecast entries."""
from __future__ import annotations
import json
from typing import List
from batchmark.forecast import ForecastEntry


def entry_to_dict(e: ForecastEntry) -> dict:
    return {
        "command": e.command,
        "sample_count": e.sample_count,
        "mean_duration": e.mean_duration,
        "predicted_next": e.predicted_next,
        "trend": e.trend,
    }


def format_forecast_json(entries: List[ForecastEntry]) -> str:
    return json.dumps([entry_to_dict(e) for e in entries], indent=2)


def format_forecast_table(entries: List[ForecastEntry]) -> str:
    if not entries:
        return "No forecast data."
    header = f"{'Command':<40} {'Samples':>7} {'Mean(s)':>9} {'Predicted(s)':>13} {'Trend':<12}"
    sep = "-" * len(header)
    rows = [header, sep]
    for e in entries:
        cmd = e.command if len(e.command) <= 40 else e.command[:37] + "..."
        rows.append(
            f"{cmd:<40} {e.sample_count:>7} {e.mean_duration:>9.4f} "
            f"{e.predicted_next:>13.4f} {e.trend:<12}"
        )
    return "\n".join(rows)
