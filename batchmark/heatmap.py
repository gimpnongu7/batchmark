from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Optional
from batchmark.runner import CommandResult

# Intensity chars from lowest to highest
_BLOCKS = " ░▒▓█"


@dataclass
class HeatmapConfig:
    buckets: int = 5
    min_duration: Optional[float] = None
    max_duration: Optional[float] = None


@dataclass
class HeatmapCell:
    command: str
    duration: float
    status: str
    intensity: int  # 0-4 index into _BLOCKS
    symbol: str


def parse_heatmap_config(raw: dict) -> HeatmapConfig:
    return HeatmapConfig(
        buckets=int(raw.get("buckets", 5)),
        min_duration=raw.get("min_duration"),
        max_duration=raw.get("max_duration"),
    )


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def build_heatmap(results: List[CommandResult], cfg: HeatmapConfig) -> List[HeatmapCell]:
    if not results:
        return []

    durations = [r.duration for r in results]
    lo = cfg.min_duration if cfg.min_duration is not None else min(durations)
    hi = cfg.max_duration if cfg.max_duration is not None else max(durations)

    cells: List[HeatmapCell] = []
    span = hi - lo
    n = max(1, cfg.buckets - 1)

    for r in results:
        if span == 0:
            idx = n // 2
        else:
            ratio = _clamp((r.duration - lo) / span, 0.0, 1.0)
            idx = round(ratio * n)
        idx = max(0, min(len(_BLOCKS) - 1, idx))
        cells.append(HeatmapCell(
            command=r.command,
            duration=r.duration,
            status=r.status,
            intensity=idx,
            symbol=_BLOCKS[idx],
        ))
    return cells


def format_heatmap_table(cells: List[HeatmapCell]) -> str:
    if not cells:
        return "(no results)"
    header = f"{'COMMAND':<40} {'DUR':>8}  {'ST':<8}  HEAT"
    sep = "-" * len(header)
    rows = [header, sep]
    for c in cells:
        cmd = c.command[:38] + ".." if len(c.command) > 40 else c.command
        rows.append(f"{cmd:<40} {c.duration:>8.3f}  {c.status:<8}  {c.symbol}")
    return "\n".join(rows)
