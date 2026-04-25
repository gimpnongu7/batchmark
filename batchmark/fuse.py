"""fuse.py — merge consecutive results from the same command into a single fused entry."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from batchmark.runner import CommandResult


@dataclass
class FuseConfig:
    strategy: str = "sum"          # sum | mean | min | max
    max_group: Optional[int] = None  # cap on how many to fuse per command


@dataclass
class FusedResult:
    command: str
    duration: float
    status: str
    count: int
    sources: List[CommandResult] = field(default_factory=list)

    @property
    def stdout(self) -> str:
        return "\n".join(r.stdout for r in self.sources if r.stdout)

    @property
    def stderr(self) -> str:
        return "\n".join(r.stderr for r in self.sources if r.stderr)


def parse_fuse_config(raw: dict) -> FuseConfig:
    strategy = raw.get("strategy", "sum")
    if strategy not in ("sum", "mean", "min", "max"):
        raise ValueError(f"Invalid fuse strategy: {strategy!r}")
    max_group = raw.get("max_group")
    if max_group is not None and max_group < 1:
        raise ValueError("max_group must be >= 1")
    return FuseConfig(strategy=strategy, max_group=max_group)


def _combine(durations: List[float], strategy: str) -> float:
    if strategy == "sum":
        return sum(durations)
    if strategy == "mean":
        return sum(durations) / len(durations)
    if strategy == "min":
        return min(durations)
    if strategy == "max":
        return max(durations)
    raise ValueError(f"Unknown strategy: {strategy}")


def _majority_status(sources: List[CommandResult]) -> str:
    statuses = [r.status for r in sources]
    if any(s == "failure" for s in statuses):
        return "failure"
    if any(s == "timeout" for s in statuses):
        return "timeout"
    return "success"


def fuse_results(results: List[CommandResult], cfg: FuseConfig) -> List[FusedResult]:
    """Group consecutive results by command and fuse each group."""
    if not results:
        return []

    fused: List[FusedResult] = []
    group: List[CommandResult] = [results[0]]

    for r in results[1:]:
        if r.command == group[0].command and (
            cfg.max_group is None or len(group) < cfg.max_group
        ):
            group.append(r)
        else:
            fused.append(_make_fused(group, cfg))
            group = [r]

    fused.append(_make_fused(group, cfg))
    return fused


def _make_fused(group: List[CommandResult], cfg: FuseConfig) -> FusedResult:
    duration = _combine([r.duration for r in group], cfg.strategy)
    status = _majority_status(group)
    return FusedResult(
        command=group[0].command,
        duration=duration,
        status=status,
        count=len(group),
        sources=list(group),
    )
