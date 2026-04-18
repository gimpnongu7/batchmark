"""Sorting utilities for CommandResult lists."""

from typing import List, Optional
from batchmark.runner import CommandResult

VALID_KEYS = ("duration", "command", "returncode", "status")


def sort_results(
    results: List[CommandResult],
    key: str = "duration",
    reverse: bool = False,
) -> List[CommandResult]:
    """Return a sorted copy of results by the given key.

    Args:
        results: List of CommandResult instances.
        key: Attribute to sort by. One of 'duration', 'command',
             'returncode', 'status'.
        reverse: If True, sort descending.

    Raises:
        ValueError: If key is not a recognised sort field.
    """
    if key not in VALID_KEYS:
        raise ValueError(
            f"Invalid sort key '{key}'. Choose from: {', '.join(VALID_KEYS)}"
        )

    def _get(r: CommandResult):
        if key == "status":
            return (0 if r.returncode == 0 else 1)
        return getattr(r, key)

    return sorted(results, key=_get, reverse=reverse)


def top_n(
    results: List[CommandResult],
    n: int,
    key: str = "duration",
    reverse: bool = True,
) -> List[CommandResult]:
    """Return the top-n results sorted by key (default: slowest first)."""
    if n < 1:
        raise ValueError("n must be at least 1")
    sorted_results = sort_results(results, key=key, reverse=reverse)
    return sorted_results[:n]
