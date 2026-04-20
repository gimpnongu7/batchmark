"""sweep_report.py — format SweepResult lists as JSON or table output."""
from __future__ import annotations

import json
from typing import List

from batchmark.sweep import SweepResult


def sweep_result_to_dict(sr: SweepResult) -> dict:
    return {
        "param_value": sr.param_value,
        "command": sr.command,
        "status": sr.status,
        "duration": round(sr.duration, 4),
        "returncode": sr.result.returncode,
    }


def format_sweep_json(results: List[SweepResult]) -> str:
    return json.dumps([sweep_result_to_dict(r) for r in results], indent=2)


def format_sweep_table(results: List[SweepResult]) -> str:
    if not results:
        return "No sweep results."

    header = f"{'PARAM VALUE':<20} {'COMMAND':<35} {'STATUS':<10} {'DURATION':>10}"
    separator = "-" * len(header)
    rows = [header, separator]

    for sr in results:
        pv = str(sr.param_value)[:18]
        cmd = sr.command[:33]
        rows.append(
            f"{pv:<20} {cmd:<35} {sr.status:<10} {sr.duration:>10.4f}s"
        )

    total = sum(r.duration for r in results)
    passed = sum(1 for r in results if r.status == "success")
    rows.append(separator)
    rows.append(
        f"{'TOTAL':<20} {len(results)} runs, {passed} passed, {total:.4f}s total"
    )
    return "\n".join(rows)
