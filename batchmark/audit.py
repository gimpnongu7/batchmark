from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from batchmark.runner import CommandResult
import datetime


@dataclass
class AuditEntry:
    command: str
    status: str
    duration: float
    timestamp: str
    run_index: int
    note: Optional[str] = None


@dataclass
class AuditLog:
    entries: List[AuditEntry] = field(default_factory=list)

    def add(self, result: CommandResult, run_index: int, note: Optional[str] = None) -> None:
        entry = AuditEntry(
            command=result.command,
            status=result.status,
            duration=result.duration,
            timestamp=datetime.datetime.utcnow().isoformat(),
            run_index=run_index,
            note=note,
        )
        self.entries.append(entry)

    def filter_by_status(self, status: str) -> List[AuditEntry]:
        return [e for e in self.entries if e.status == status]

    def commands(self) -> List[str]:
        return list(dict.fromkeys(e.command for e in self.entries))


def build_audit_log(
    results: List[CommandResult],
    run_index: int = 0,
    note: Optional[str] = None,
) -> AuditLog:
    log = AuditLog()
    for r in results:
        log.add(r, run_index=run_index, note=note)
    return log


def merge_audit_logs(logs: List[AuditLog]) -> AuditLog:
    merged = AuditLog()
    for log in logs:
        merged.entries.extend(log.entries)
    return merged
