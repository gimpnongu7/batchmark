from __future__ import annotations
import json
from typing import List
from batchmark.audit import AuditLog, AuditEntry


def entry_to_dict(entry: AuditEntry) -> dict:
    return {
        "command": entry.command,
        "status": entry.status,
        "duration": round(entry.duration, 4),
        "timestamp": entry.timestamp,
        "run_index": entry.run_index,
        "note": entry.note,
    }


def format_audit_json(log: AuditLog) -> str:
    return json.dumps([entry_to_dict(e) for e in log.entries], indent=2)


def format_audit_table(log: AuditLog) -> str:
    if not log.entries:
        return "No audit entries."
    header = f"{'#':<5} {'Command':<30} {'Status':<10} {'Duration':>10}  {'Timestamp'}"
    sep = "-" * len(header)
    rows = [
        f"{e.run_index:<5} {e.command:<30} {e.status:<10} {e.duration:>10.4f}  {e.timestamp}"
        for e in log.entries
    ]
    return "\n".join([header, sep] + rows)


def audit_summary(log: AuditLog) -> dict:
    total = len(log.entries)
    passed = sum(1 for e in log.entries if e.status == "success")
    failed = total - passed
    durations = [e.duration for e in log.entries]
    mean = sum(durations) / total if total else 0.0
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "mean_duration": round(mean, 4),
    }
