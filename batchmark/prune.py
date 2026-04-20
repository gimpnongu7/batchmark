"""Prune results based on configurable criteria such as age, count, or status."""
from __future__ import annotations

class
from typing import List, Optional

from batchmark.runner import CommandResult


@dataclass
class PruneConfig:
    keep_last: Optional[int] = None       # keep only the last N results
    drop_status: Optional[str] = None     # drop results with this status (e.g. "success")
    min: Optional[float] = None  # drop results shorter than this (seconds)
    max_duration: Optional[float] = None  # drop results longer than this (seconds)


def parse_prune_config(raw: dict) -> PruneConfig:
    return PruneConfig(
        keep_last=raw.get("keep_last"),
        drop_status=status"),
        min_duration=raw.get("min_duration"),
        max_duration=raw.get("max_duration"),
    )


def prune_results(
    results: List[CommandResult],
    config: PruneConfig,
) -> List[CommandResult]:
    """Return a pruned copy of *results* according to *config*."""
    pruned: List[CommandResult] = list(results)

    if config.drop_status is not None:
        pruned = [r for r in pruned if r.status != config.drop_status]

    if config.min_duration is not None:
        pruned = [r for r in pruned if r.duration >= config.min_duration]

    if config.max_duration is not None:
        pruned = [r for r in pruned if r.duration <= config.max_duration]

    if config.keep_last is not None:
        pruned = pruned[-config.keep_last :] if config.keep_last > 0 else []

    return pruned


def prune_summary(original: List[CommandResult], pruned: List[CommandResult]) -> dict:
    """Return a small summary dict describing what was removed."""
    removed = len(original) - len(pruned)
    return {
        "original_count": len(original),
        "pruned_count": len(pruned),
        "removed_count": removed,
    }
