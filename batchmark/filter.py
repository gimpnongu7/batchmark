"""Filtering utilities for CommandResult lists."""

from typing import List, Optional
from batchmark.runner import CommandResult


def filter_results(
    results: List[CommandResult],
    status: Optional[str] = None,
    min_duration: Optional[float] = None,
    max_duration: Optional[float] = None,
    name_contains: Optional[str] = None,
) -> List[CommandResult]:
    """Filter a list of CommandResult objects by various criteria.

    Args:
        results: List of CommandResult to filter.
        status: If given, keep only results with this status ('success', 'failure', 'timeout').
        min_duration: If given, keep only results with duration >= min_duration.
        max_duration: If given, keep only results with duration <= max_duration.
        name_contains: If given, keep only results whose command contains this substring.

    Returns:
        Filtered list of CommandResult.
    """
    filtered = results

    if status is not None:
        filtered = [r for r in filtered if r.status == status]

    if min_duration is not None:
        filtered = [r for r in filtered if r.duration >= min_duration]

    if max_duration is not None:
        filtered = [r for r in filtered if r.duration <= max_duration]

    if name_contains is not None:
        filtered = [r for r in filtered if name_contains in r.command]

    return filtered


def partition_results(results: List[CommandResult]):
    """Split results into (successes, failures, timeouts)."""
    successes = [r for r in results if r.status == "success"]
    failures = [r for r in results if r.status == "failure"]
    timeouts = [r for r in results if r.status == "timeout"]
    return successes, failures, timeouts
