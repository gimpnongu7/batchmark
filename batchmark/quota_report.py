from __future__ import annotations
import json
from batchmark.quota import QuotaState
from batchmark.runner import CommandResult
from typing import List


def quota_state_to_dict(state: QuotaState) -> dict:
    return {
        "commands_run": state.commands_run,
        "failures": state.failures,
        "total_duration": round(state.total_duration, 4),
        "stopped_reason": state.stopped_reason,
        "quota": {
            "max_failures": state.config.max_failures,
            "max_duration": state.config.max_duration,
            "max_commands": state.config.max_commands,
        },
    }


def format_quota_json(results: List[CommandResult], state: QuotaState) -> str:
    rows = [
        {"command": r.command, "status": r.status, "duration": round(r.duration, 4)}
        for r in results
    ]
    return json.dumps({"results": rows, "quota_summary": quota_state_to_dict(state)}, indent=2)


def format_quota_table(results: List[CommandResult], state: QuotaState) -> str:
    lines = [f"{'COMMAND':<40} {'STATUS':<10} {'DURATION':>10}"]
    lines.append("-" * 64)
    for r in results:
        lines.append(f"{r.command:<40} {r.status:<10} {r.duration:>10.4f}")
    lines.append("-" * 64)
    lines.append(f"Commands run : {state.commands_run}")
    lines.append(f"Failures     : {state.failures}")
    lines.append(f"Total time   : {state.total_duration:.4f}s")
    if state.stopped_reason:
        lines.append(f"Stopped      : {state.stopped_reason}")
    return "\n".join(lines)
