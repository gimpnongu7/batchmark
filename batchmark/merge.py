"""Merge multiple result lists into one, with optional deduplication and source tagging."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from batchmark.runner import CommandResult


@dataclass
class MergeConfig:
    dedupe: bool = False          # keep only first occurrence per command
    tag_source: bool = False      # attach __source__ index to extra field
    sources: List[str] = field(default_factory=list)  # optional labels per run


def parse_merge_config(raw: dict) -> MergeConfig:
    return MergeConfig(
        dedupe=raw.get("dedupe", False),
        tag_source=raw.get("tag_source", False),
        sources=raw.get("sources", []),
    )


def merge_runs(
    runs: List[List[CommandResult]],
    config: Optional[MergeConfig] = None,
) -> List[CommandResult]:
    """Flatten multiple runs into a single list."""
    if config is None:
        config = MergeConfig()

    merged: List[CommandResult] = []
    seen: set = set()

    for idx, run in enumerate(runs):
        label = config.sources[idx] if idx < len(config.sources) else str(idx)
        for result in run:
            if config.dedupe:
                if result.command in seen:
                    continue
                seen.add(result.command)
            if config.tag_source:
                # store source label in a new result with annotated command field
                # we wrap via a lightweight approach: copy dataclass
                result = _tag(result, label)
            merged.append(result)

    return merged


def _tag(result: CommandResult, source: str) -> CommandResult:
    """Return a shallow copy of result with source appended to command string."""
    # CommandResult is a dataclass; rebuild with tagged command representation
    import dataclasses
    d = dataclasses.asdict(result)
    d["command"] = f"[{source}] {result.command}"
    return CommandResult(**d)
