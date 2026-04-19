"""Pin specific commands to always run first or last in a batch."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
from batchmark.runner import CommandResult


@dataclass
class PinConfig:
    first: List[str] = field(default_factory=list)
    last: List[str] = field(default_factory=list)


def parse_pin_config(raw: dict) -> PinConfig:
    pin = raw.get("pin", {})
    return PinConfig(
        first=pin.get("first", []),
        last=pin.get("last", []),
    )


def pin_commands(commands: List[str], config: PinConfig) -> List[str]:
    """Reorder commands so pinned-first come first, pinned-last come last."""
    first_set = list(config.first)
    last_set = list(config.last)
    pinned = set(first_set) | set(last_set)
    middle = [c for c in commands if c not in pinned]
    ordered_first = [c for c in first_set if c in commands]
    ordered_last = [c for c in last_set if c in commands]
    return ordered_first + middle + ordered_last


def pin_results(results: List[CommandResult], config: PinConfig) -> List[CommandResult]:
    """Reorder results matching pin_commands logic."""
    commands = [r.command for r in results]
    order = pin_commands(commands, config)
    index = {r.command: r for r in results}
    seen = set()
    out = []
    for cmd in order:
        if cmd in index and cmd not in seen:
            out.append(index[cmd])
            seen.add(cmd)
    for r in results:
        if r.command not in seen:
            out.append(r)
    return out
