"""absorb.py — merge overlapping time windows by collapsing results within a gap threshold."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from batchmark.runner import CommandResult


@dataclass
class AbsorbConfig:
    gap_seconds: float = 0.5
    strategy: str = "fastest"  # fastest | first | last
    include_absorbed: bool = False


@dataclass
class AbsorbedGroup:
    representative: CommandResult
    absorbed: List[CommandResult] = field(default_factory=list)

    @property
    def command(self) -> str:
        return self.representative.command

    @property
    def duration(self) -> float:
        return self.representative.duration

    @property
    def total_absorbed(self) -> int:
        return len(self.absorbed)


def parse_absorb_config(raw: dict) -> AbsorbConfig:
    cfg = raw.get("absorb", {})
    strategy = cfg.get("strategy", "fastest")
    if strategy not in ("fastest", "first", "last"):
        raise ValueError(f"absorb strategy must be fastest/first/last, got {strategy!r}")
    gap = cfg.get("gap_seconds", 0.5)
    if gap < 0:
        raise ValueError("absorb gap_seconds must be >= 0")
    return AbsorbConfig(
        gap_seconds=gap,
        strategy=strategy,
        include_absorbed=cfg.get("include_absorbed", False),
    )


def _pick(group: List[CommandResult], strategy: str) -> CommandResult:
    if strategy == "fastest":
        return min(group, key=lambda r: r.duration)
    if strategy == "last":
        return group[-1]
    return group[0]  # first


def absorb_results(
    results: List[CommandResult],
    config: Optional[AbsorbConfig] = None,
) -> List[AbsorbedGroup]:
    if config is None:
        config = AbsorbConfig()

    if not results:
        return []

    # group consecutive results for the same command within gap_seconds
    groups: List[AbsorbedGroup] = []
    pending: List[CommandResult] = [results[0]]

    for prev, curr in zip(results, results[1:]):
        same_command = prev.command == curr.command
        within_gap = abs(curr.duration - prev.duration) <= config.gap_seconds
        if same_command and within_gap:
            pending.append(curr)
        else:
            rep = _pick(pending, config.strategy)
            absorbed = [r for r in pending if r is not rep]
            groups.append(AbsorbedGroup(representative=rep, absorbed=absorbed))
            pending = [curr]

    rep = _pick(pending, config.strategy)
    absorbed = [r for r in pending if r is not rep]
    groups.append(AbsorbedGroup(representative=rep, absorbed=absorbed))

    return groups
