"""clip.py — clamp result counts per status bucket to a maximum cap."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from batchmark.runner import CommandResult


@dataclass
class ClipConfig:
    max_per_status: Dict[str, int] = field(default_factory=dict)
    max_total: Optional[int] = None
    keep: str = "first"  # "first" | "last"


def parse_clip_config(raw: dict) -> ClipConfig:
    keep = raw.get("keep", "first")
    if keep not in ("first", "last"):
        raise ValueError(f"clip.keep must be 'first' or 'last', got {keep!r}")
    max_total = raw.get("max_total")
    if max_total is not None and max_total < 1:
        raise ValueError("clip.max_total must be >= 1")
    per_status = raw.get("max_per_status", {})
    for status, limit in per_status.items():
        if limit < 1:
            raise ValueError(f"clip.max_per_status[{status!r}] must be >= 1")
    return ClipConfig(max_per_status=per_status, max_total=max_total, keep=keep)


def clip_results(
    results: List[CommandResult], cfg: ClipConfig
) -> List[CommandResult]:
    """Return results with per-status and total caps applied."""
    if cfg.keep == "last":
        results = list(reversed(results))

    counts: Dict[str, int] = {}
    clipped: List[CommandResult] = []

    for r in results:
        status = r.status
        counts[status] = counts.get(status, 0) + 1
        limit = cfg.max_per_status.get(status)
        if limit is not None and counts[status] > limit:
            continue
        if cfg.max_total is not None and len(clipped) >= cfg.max_total:
            break
        clipped.append(r)

    if cfg.keep == "last":
        clipped = list(reversed(clipped))

    return clipped


def clip_summary(original: List[CommandResult], clipped: List[CommandResult]) -> dict:
    return {
        "original_count": len(original),
        "clipped_count": len(clipped),
        "dropped": len(original) - len(clipped),
    }
