from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Optional
from batchmark.runner import CommandResult
from batchmark.stats import compute_stats, BatchStats


@dataclass
class RollupGroup:
    name: str
    results: List[CommandResult]
    stats: BatchStats

    @property
    def command_count(self) -> int:
        return len(self.results)

    @property
    def success_rate(self) -> float:
        if not self.results:
            return 0.0
        ok = sum(1 for r in self.results if r.status == "success")
        return ok / len(self.results)


@dataclass
class RollupConfig:
    group_by: str = "status"  # "status" | "prefix" | "tag"
    prefix_delimiter: str = ":"
    min_group_size: int = 1


def parse_rollup_config(raw: dict) -> RollupConfig:
    return RollupConfig(
        group_by=raw.get("group_by", "status"),
        prefix_delimiter=raw.get("prefix_delimiter", ":"),
        min_group_size=int(raw.get("min_group_size", 1)),
    )


def _group_key(result: CommandResult, cfg: RollupConfig) -> str:
    if cfg.group_by == "status":
        return result.status
    if cfg.group_by == "prefix":
        parts = result.command.split(cfg.prefix_delimiter, 1)
        return parts[0].strip() if len(parts) > 1 else "other"
    return "all"


def rollup(results: List[CommandResult], cfg: Optional[RollupConfig] = None) -> List[RollupGroup]:
    if cfg is None:
        cfg = RollupConfig()
    buckets: Dict[str, List[CommandResult]] = {}
    for r in results:
        key = _group_key(r, cfg)
        buckets.setdefault(key, []).append(r)
    groups = []
    for name, members in buckets.items():
        if len(members) < cfg.min_group_size:
            continue
        groups.append(RollupGroup(name=name, results=members, stats=compute_stats(members)))
    groups.sort(key=lambda g: g.name)
    return groups
