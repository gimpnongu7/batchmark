"""Track high-water and low-water marks across benchmark runs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from batchmark.runner import CommandResult


@dataclass
class WatermarkConfig:
    track: str = "both"  # "high", "low", or "both"
    metric: str = "duration"  # only "duration" supported for now


@dataclass
class WatermarkEntry:
    command: str
    high: Optional[float]  # worst (slowest) observed
    low: Optional[float]   # best (fastest) observed
    current: float
    high_broken: bool = False  # current exceeded previous high
    low_broken: bool = False   # current beat previous low


def parse_watermark_config(raw: dict) -> WatermarkConfig:
    return WatermarkConfig(
        track=raw.get("track", "both"),
        metric=raw.get("metric", "duration"),
    )


def _index_baseline(baseline: List[Dict]) -> Dict[str, Dict]:
    """Turn a list of baseline dicts into a command-keyed map."""
    return {entry["command"]: entry for entry in baseline}


def compute_watermarks(
    results: List[CommandResult],
    baseline: Optional[List[Dict]],
    cfg: WatermarkConfig,
) -> List[WatermarkEntry]:
    """Compare results against stored watermarks."""
    indexed = _index_baseline(baseline) if baseline else {}
    entries: List[WatermarkEntry] = []

    for r in results:
        prev = indexed.get(r.command, {})
        prev_high: Optional[float] = prev.get("high")
        prev_low: Optional[float] = prev.get("low")
        current = r.duration

        high_broken = prev_high is not None and current > prev_high
        low_broken = prev_low is not None and current < prev_low

        new_high = max(current, prev_high) if prev_high is not None else current
        new_low = min(current, prev_low) if prev_low is not None else current

        entries.append(WatermarkEntry(
            command=r.command,
            high=new_high if cfg.track in ("high", "both") else None,
            low=new_low if cfg.track in ("low", "both") else None,
            current=current,
            high_broken=high_broken,
            low_broken=low_broken,
        ))

    return entries


def watermarks_to_dicts(entries: List[WatermarkEntry]) -> List[Dict]:
    return [
        {
            "command": e.command,
            "current": round(e.current, 4),
            "high": round(e.high, 4) if e.high is not None else None,
            "low": round(e.low, 4) if e.low is not None else None,
            "high_broken": e.high_broken,
            "low_broken": e.low_broken,
        }
        for e in entries
    ]
