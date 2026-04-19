"""Deduplication utilities for batchmark command results."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Literal
from batchmark.runner import CommandResult

Strategy = Literal["first", "last", "fastest", "slowest"]


@dataclass
class DedupeConfig:
    strategy: Strategy = "first"
    case_sensitive: bool = True


def _key(result: CommandResult, case_sensitive: bool) -> str:
    cmd = result.command
    return cmd if case_sensitive else cmd.lower()


def dedupe_results(
    results: List[CommandResult],
    config: DedupeConfig | None = None,
) -> List[CommandResult]:
    """Return a deduplicated list of results based on command string."""
    if config is None:
        config = DedupeConfig()

    strategy = config.strategy
    seen: Dict[str, CommandResult] = {}

    for r in results:
        k = _key(r, config.case_sensitive)
        if k not in seen:
            seen[k] = r
        else:
            existing = seen[k]
            if strategy == "last":
                seen[k] = r
            elif strategy == "fastest":
                if r.duration < existing.duration:
                    seen[k] = r
            elif strategy == "slowest":
                if r.duration > existing.duration:
                    seen[k] = r
            # "first" keeps existing — no update needed

    # preserve original order of winning entries
    order = {id(v): i for i, v in enumerate(seen.values())}
    return sorted(seen.values(), key=lambda r: order[id(r)])


def count_duplicates(results: List[CommandResult], case_sensitive: bool = True) -> Dict[str, int]:
    """Return a mapping of command -> occurrence count for commands seen more than once."""
    counts: Dict[str, int] = {}
    for r in results:
        k = _key(r, case_sensitive)
        counts[k] = counts.get(k, 0) + 1
    return {k: v for k, v in counts.items() if v > 1}
