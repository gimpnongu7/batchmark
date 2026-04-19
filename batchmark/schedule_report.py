from __future__ import annotations
from typing import List
import json

from batchmark.schedule import ScheduleResult


def schedule_results_to_dicts(results: List[ScheduleResult]) -> List[dict]:
    out = []
    for sr in results:
        out.append({
            "command": sr.entry.command,
            "tags": sr.entry.tags,
            "delay": sr.entry.delay,
            "status": sr.result.status,
            "duration": round(sr.result.duration, 4),
            "wait_time": round(sr.wait_time, 4),
            "returncode": sr.result.returncode,
            "stdout": sr.result.stdout,
            "stderr": sr.result.stderr,
        })
    return out


def format_schedule_json(results: List[ScheduleResult]) -> str:
    return json.dumps({"schedule_results": schedule_results_to_dicts(results)}, indent=2)


def format_schedule_table(results: List[ScheduleResult]) -> str:
    header = f"{'COMMAND':<30} {'STATUS':<10} {'DURATION':>10} {'WAIT':>8} {'TAGS'}"
    sep = "-" * len(header)
    lines = [header, sep]
    for sr in results:
        tags = ",".join(sr.entry.tags) if sr.entry.tags else "-"
        lines.append(
            f"{sr.entry.command:<30} {sr.result.status:<10} "
            f"{sr.result.duration:>10.4f} {sr.wait_time:>8.4f} {tags}"
        )
    return "\n".join(lines)
