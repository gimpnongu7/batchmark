"""Cap module: limit the maximum number of results kept per status category."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from batchmark.runner import CommandResult


@dataclass
class CapConfig:
    per_status: Dict[str, int]
    default: Optional[int] = None


def parse_cap_config(raw: dict) -> CapConfig:
    """Parse a raw config dict into a CapConfig."""
    per_status = raw.get("per_status", {})
    if not isinstance(per_status, dict):
        raise ValueError("per_status must be a mapping of status -> int")
    per_status = {str(k): int(v) for k, v in per_status.items()}
    default = raw.get("default")
    if default is not None:
        default = int(default)
    return CapConfig(per_status=per_status, default=default)


def cap_results(results: List[CommandResult], config: CapConfig) -> List[CommandResult]:
    """Return results with at most `cap` entries per status bucket.

    Order of results is preserved; excess entries are dropped from the tail.
    """
    counts: Dict[str, int] = {}
    kept: List[CommandResult] = []

    for result in results:
        status = result.status
        limit = config.per_status.get(status, config.default)
        if limit is None:
            kept.append(result)
            continue
        current = counts.get(status, 0)
        if current < limit:
            kept.append(result)
            counts[status] = current + 1

    return kept


def cap_summary(original: List[CommandResult], capped: List[CommandResult]) -> Dict[str, int]:
    """Return a dict mapping status -> number of results dropped."""
    from collections import Counter

    orig_counts: Counter = Counter(r.status for r in original)
    kept_counts: Counter = Counter(r.status for r in capped)
    dropped = {}
    for status, total in orig_counts.items():
        diff = total - kept_counts.get(status, 0)
        if diff > 0:
            dropped[status] = diff
    return dropped
