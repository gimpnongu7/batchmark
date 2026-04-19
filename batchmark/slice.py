"""Slice a list of CommandResults by index range or time range."""
from dataclasses import dataclass
from typing import List, Optional
from batchmark.runner import CommandResult


@dataclass
class SliceConfig:
    start: int = 0
    stop: Optional[int] = None
    step: int = 1
    min_time: Optional[float] = None  # wall-clock start offset filter
    max_time: Optional[float] = None


def parse_slice_config(raw: dict) -> SliceConfig:
    return SliceConfig(
        start=raw.get("start", 0),
        stop=raw.get("stop", None),
        step=max(1, raw.get("step", 1)),
        min_time=raw.get("min_time", None),
        max_time=raw.get("max_time", None),
    )


def slice_results(
    results: List[CommandResult],
    cfg: SliceConfig,
) -> List[CommandResult]:
    """Apply index-based slicing first, then optional duration filters."""
    sliced = results[cfg.start : cfg.stop : cfg.step]

    if cfg.min_time is not None:
        sliced = [r for r in sliced if r.duration >= cfg.min_time]
    if cfg.max_time is not None:
        sliced = [r for r in sliced if r.duration <= cfg.max_time]

    return sliced


def slice_head(results: List[CommandResult], n: int) -> List[CommandResult]:
    """Return first n results."""
    return results[:n]


def slice_tail(results: List[CommandResult], n: int) -> List[CommandResult]:
    """Return last n results."""
    return results[-n:] if n else []


def slice_every(results: List[CommandResult], step: int) -> List[CommandResult]:
    """Return every step-th result starting from index 0."""
    if step < 1:
        raise ValueError("step must be >= 1")
    return results[::step]
