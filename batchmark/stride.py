"""stride.py — run every Nth result from a batch (step sampling)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from batchmark.runner import CommandResult


@dataclass
class StrideConfig:
    step: int = 1
    offset: int = 0
    max_results: Optional[int] = None


def parse_stride_config(raw: dict) -> StrideConfig:
    step = int(raw.get("step", 1))
    if step < 1:
        raise ValueError(f"stride step must be >= 1, got {step}")
    offset = int(raw.get("offset", 0))
    if offset < 0:
        raise ValueError(f"stride offset must be >= 0, got {offset}")
    max_results = raw.get("max_results")
    if max_results is not None:
        max_results = int(max_results)
        if max_results < 0:
            raise ValueError(f"max_results must be >= 0, got {max_results}")
    return StrideConfig(step=step, offset=offset, max_results=max_results)


def stride_results(
    results: List[CommandResult],
    cfg: StrideConfig,
) -> List[CommandResult]:
    """Return every cfg.step-th result starting from cfg.offset."""
    if not results:
        return []
    selected = results[cfg.offset :: cfg.step]
    if cfg.max_results is not None:
        selected = selected[: cfg.max_results]
    return selected


def stride_summary(original: List[CommandResult], strided: List[CommandResult]) -> str:
    kept = len(strided)
    total = len(original)
    dropped = total - kept
    return (
        f"stride: kept {kept}/{total} results "
        f"({dropped} dropped, step={kept and total // max(kept, 1)})"
    )
