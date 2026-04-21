from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
from batchmark.runner import CommandResult


@dataclass
class ReorderConfig:
    priority: List[str]  # commands to move to front
    reverse: bool = False
    stable: bool = True


def parse_reorder_config(raw: dict) -> ReorderConfig:
    return ReorderConfig(
        priority=raw.get("priority", []),
        reverse=raw.get("reverse", False),
        stable=raw.get("stable", True),
    )


def reorder_results(
    results: List[CommandResult],
    config: ReorderConfig,
) -> List[CommandResult]:
    """Reorder results according to the given config.

    Priority commands are moved to the front in the order they appear in
    ``config.priority``. If ``config.reverse`` is True the entire list is
    reversed after that.
    """
    priority_set = set(config.priority)
    front = []
    rest = []
    for r in results:
        if r.command in priority_set:
            front.append(r)
        else:
            rest.append(r)

    # preserve declared priority order for front items
    order_map = {cmd: i for i, cmd in enumerate(config.priority)}
    front.sort(key=lambda r: order_map.get(r.command, len(config.priority)))

    combined = front + rest
    if config.reverse:
        combined = list(reversed(combined))
    return combined


def move_to_back(
    results: List[CommandResult],
    commands: List[str],
) -> List[CommandResult]:
    """Move the specified commands to the end of the results list."""
    back_set = set(commands)
    front = [r for r in results if r.command not in back_set]
    back = [r for r in results if r.command in back_set]
    return front + back


def deduplicate_results(
    results: List[CommandResult],
    keep: str = "first",
) -> List[CommandResult]:
    """Remove duplicate entries for the same command.

    Args:
        results: The list of results to deduplicate.
        keep: Which occurrence to keep – ``"first"`` (default) or ``"last"``.

    Returns:
        A new list with at most one result per command.
    """
    if keep not in ("first", "last"):
        raise ValueError(f"keep must be 'first' or 'last', got {keep!r}")

    seen: dict[str, CommandResult] = {}
    for r in results:
        if keep == "first" and r.command in seen:
            continue
        seen[r.command] = r

    # preserve original relative order of the kept entries
    order = list(seen.keys())
    return [seen[cmd] for cmd in order]
