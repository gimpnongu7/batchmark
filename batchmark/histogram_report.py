from __future__ import annotations
import json
from typing import List
from batchmark.histogram import HistogramBin, HistogramConfig


def bin_to_dict(b: HistogramBin) -> dict:
    return {
        "range": b.label,
        "low": b.low,
        "high": b.high,
        "count": b.count,
        "commands": b.commands,
    }


def format_histogram_json(bins: List[HistogramBin]) -> str:
    return json.dumps([bin_to_dict(b) for b in bins], indent=2)


def format_histogram_table(
    bins: List[HistogramBin],
    config: HistogramConfig | None = None,
) -> str:
    from batchmark.histogram import HistogramConfig

    if config is None:
        config = HistogramConfig()

    if not bins:
        return "(no data)"

    max_count = max(b.count for b in bins) or 1
    bar_width = config.bar_width
    lines = [f"{'Range':<22}  {'Count':>5}  Bar"]
    lines.append("-" * (22 + 5 + bar_width + 6))

    for b in bins:
        filled = int(b.count / max_count * bar_width)
        bar = "█" * filled + " " * (bar_width - filled)
        lines.append(f"{b.label:<22}  {b.count:>5}  |{bar}|")

    return "\n".join(lines)


def histogram_summary(bins: List[HistogramBin]) -> str:
    total = sum(b.count for b in bins)
    non_empty = sum(1 for b in bins if b.count > 0)
    peak = max(bins, key=lambda b: b.count, default=None)
    lines = [
        f"Total results : {total}",
        f"Non-empty bins: {non_empty}/{len(bins)}",
    ]
    if peak:
        lines.append(f"Peak bin      : {peak.label} ({peak.count} results)")
    return "\n".join(lines)
