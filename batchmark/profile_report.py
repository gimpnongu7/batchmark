"""Helpers to merge profile snapshots into existing reports."""
from __future__ import annotations
from typing import List, Optional, Tuple
import json

from batchmark.runner import CommandResult
from batchmark.profile import ProfileSnapshot, profile_to_dict, format_profile_table


def attach_profiles(
    results: List[CommandResult],
    snapshots: List[ProfileSnapshot],
) -> List[Tuple[CommandResult, Optional[ProfileSnapshot]]]:
    """Zip results with matching snapshots by command name (first match)."""
    index: dict[str, ProfileSnapshot] = {}
    for snap in snapshots:
        index.setdefault(snap.command, snap)
    return [(r, index.get(r.command)) for r in results]


def enrich_result_dict(result_dict: dict, snap: Optional[ProfileSnapshot]) -> dict:
    """Add a 'profile' key to an existing result dict."""
    out(result_dict)
    out["profile"] = profile_to_dict(snap) if snap is not None else None
    return out


def format_json_with_profiles(
    results: List[CommandResult],
    snapshots: List[ProfileSnapshot],
) -> str:
    from batchmark.report import results_to_dict
    base = results_to_dict(results)
    paired = attach_profiles(results, snapshots)
    enriched = []
    for (r, snap), entry in zip(paired, base["results"]):
        enriched.append(enrich_result_dict(entry, snap))
    base["results"] = enriched
    return json.dumps(base, indent=2)


def format_table_with_profiles(
    results: List[CommandResult],
    snapshots: List[ProfileSnapshot],
) -> str:
    from batchmark.report import format_table
    base_table = format_table(results)
    profile_section = "\n\n=== Profile Summary ===\n" + format_profile_table(snapshots)
    return base_table + profile_section
