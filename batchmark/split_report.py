"""Reporting helpers for SplitResult."""
from __future__ import annotations
import json
from typing import Any, Dict, List
from batchmark.split import SplitResult
from batchmark.report import results_to_dict


def split_result_to_dicts(sr: SplitResult) -> Dict[str, Any]:
    """Return a dict mapping group name -> list of result dicts."""
    return {
        group: [results_to_dict([r])["results"][0] for r in results]
        for group, results in sr.groups.items()
    }


def format_split_json(sr: SplitResult) -> str:
    return json.dumps(split_result_to_dicts(sr), indent=2)


def format_split_table(sr: SplitResult) -> str:
    lines: List[str] = []
    for group, results in sr.groups.items():
        lines.append(f"=== {group} ({len(results)} result(s)) ===")
        lines.append(f"  {'COMMAND':<40} {'STATUS':<10} {'DURATION':>10}")
        lines.append("  " + "-" * 64)
        for r in results:
            cmd = r.command[:38] + ".." if len(r.command) > 40 else r.command
            lines.append(f"  {cmd:<40} {r.status:<10} {r.duration:>9.3f}s")
        lines.append("")
    return "\n".join(lines)
