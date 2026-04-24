"""evict.py — drop results from a batch based on age or run-count thresholds."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from batchmark.runner import CommandResult


@dataclass
class EvictConfig:
    max_results: Optional[int] = None   # keep at most N most-recent results
    max_duration: Optional[float] = None  # drop results whose duration exceeds this
    drop_failures: bool = False           # drop all non-success results
    drop_timeouts: bool = False           # drop timeout results specifically


def parse_evict_config(raw: dict) -> EvictConfig:
    return EvictConfig(
        max_results=raw.get("max_results"),
        max_duration=raw.get("max_duration"),
        drop_failures=bool(raw.get("drop_failures", False)),
        drop_timeouts=bool(raw.get("drop_timeouts", False)),
    )


def _should_evict(result: CommandResult, cfg: EvictConfig) -> bool:
    if cfg.drop_timeouts and result.status == "timeout":
        return True
    if cfg.drop_failures and result.status != "success":
        return True
    if cfg.max_duration is not None and result.duration > cfg.max_duration:
        return True
    return False


def evict_results(
    results: List[CommandResult],
    cfg: EvictConfig,
) -> List[CommandResult]:
    """Return a filtered list with eviction rules applied."""
    kept = [r for r in results if not _should_evict(r, cfg)]
    if cfg.max_results is not None and len(kept) > cfg.max_results:
        kept = kept[-cfg.max_results:]  # keep the most-recent N
    return kept


def evict_summary(original: List[CommandResult], evicted: List[CommandResult]) -> dict:
    removed = len(original) - len(evicted)
    return {
        "original_count": len(original),
        "remaining_count": len(evicted),
        "evicted_count": removed,
    }
