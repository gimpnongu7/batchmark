"""Flatten nested batch results from matrix/pipeline runs into a single list."""
from dataclasses import dataclass
from typing import List, Any

from batchmark.runner import CommandResult


@dataclass
class FlattenConfig:
    add_source_tag: bool = True
    source_key: str = "source"


def flatten_groups(groups: dict) -> List[CommandResult]:
    """Flatten a dict of {group_name: [CommandResult]} into a single list."""
    out = []
    for results in groups.values():
        out.extend(results)
    return out


def flatten_with_tags(groups: dict, cfg: FlattenConfig = None) -> List[dict]:
    """Flatten groups into dicts, optionally tagging each result with its source group."""
    if cfg is None:
        cfg = FlattenConfig()
    out = []
    for group_name, results in groups.items():
        for r in results:
            d: dict = {
                "command": r.command,
                "returncode": r.returncode,
                "duration": r.duration,
                "stdout": r.stdout,
                "stderr": r.stderr,
                "timed_out": r.timed_out,
            }
            if cfg.add_source_tag:
                d[cfg.source_key] = group_name
            out.append(d)
    return out


def parse_flatten_config(raw: dict) -> FlattenConfig:
    section = raw.get("flatten", {})
    return FlattenConfig(
        add_source_tag=section.get("add_source_tag", True),
        source_key=section.get("source_key", "source"),
    )
