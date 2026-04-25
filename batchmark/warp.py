"""warp.py — apply a time-scaling transform to result durations.

Useful for simulating faster/slower environments or normalizing results
to a reference machine speed factor.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from batchmark.runner import CommandResult


@dataclass
class WarpConfig:
    factor: float = 1.0          # multiply every duration by this value
    min_duration: float = 0.0    # floor after scaling
    max_duration: Optional[float] = None  # ceiling after scaling (None = no cap)


@dataclass
class WarpedResult:
    original: CommandResult
    warped_duration: float

    @property
    def command(self) -> str:
        return self.original.command

    @property
    def status(self) -> str:
        return self.original.status


def parse_warp_config(raw: dict) -> WarpConfig:
    factor = float(raw.get("factor", 1.0))
    if factor <= 0:
        raise ValueError(f"warp factor must be > 0, got {factor}")
    min_dur = float(raw.get("min_duration", 0.0))
    max_raw = raw.get("max_duration")
    max_dur = float(max_raw) if max_raw is not None else None
    return WarpConfig(factor=factor, min_duration=min_dur, max_duration=max_dur)


def _warp_duration(duration: float, cfg: WarpConfig) -> float:
    scaled = duration * cfg.factor
    scaled = max(scaled, cfg.min_duration)
    if cfg.max_duration is not None:
        scaled = min(scaled, cfg.max_duration)
    return round(scaled, 6)


def warp_results(results: List[CommandResult], cfg: WarpConfig) -> List[WarpedResult]:
    return [WarpedResult(original=r, warped_duration=_warp_duration(r.duration, cfg))
            for r in results]


def warp_summary(warped: List[WarpedResult]) -> dict:
    if not warped:
        return {"count": 0, "total_original": 0.0, "total_warped": 0.0, "factor_applied": None}
    total_orig = sum(w.original.duration for w in warped)
    total_warp = sum(w.warped_duration for w in warped)
    return {
        "count": len(warped),
        "total_original": round(total_orig, 6),
        "total_warped": round(total_warp, 6),
        "speedup": round(total_orig / total_warp, 4) if total_warp > 0 else None,
    }
