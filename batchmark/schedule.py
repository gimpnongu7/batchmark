from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Callable
import time

from batchmark.runner import CommandResult, run_batch


@dataclass
class ScheduleEntry:
    command: str
    delay: float = 0.0  # seconds before running
    tags: List[str] = field(default_factory=list)


@dataclass
class ScheduleConfig:
    entries: List[ScheduleEntry]
    max_concurrency: int = 1
    global_delay: float = 0.0  # extra delay between each entry


@dataclass
class ScheduleResult:
    entry: ScheduleEntry
    result: CommandResult
    scheduled_at: float
    started_at: float

    @property
    def wait_time(self) -> float:
        return self.started_at - self.scheduled_at


def parse_schedule_config(raw: dict) -> ScheduleConfig:
    entries = []
    for item in raw.get("entries", []):
        entries.append(ScheduleEntry(
            command=item["command"],
            delay=float(item.get("delay", 0.0)),
            tags=item.get("tags", []),
        ))
    return ScheduleConfig(
        entries=entries,
        max_concurrency=int(raw.get("max_concurrency", 1)),
        global_delay=float(raw.get("global_delay", 0.0)),
    )


def run_schedule(
    config: ScheduleConfig,
    timeout: Optional[float] = None,
    on_result: Optional[Callable[[ScheduleResult], None]] = None,
) -> List[ScheduleResult]:
    results = []
    for i, entry in enumerate(config.entries):
        if i > 0 and config.global_delay > 0:
            time.sleep(config.global_delay)
        if entry.delay > 0:
            time.sleep(entry.delay)
        scheduled_at = time.monotonic()
        started_at = time.monotonic()
        batch = run_batch([entry.command], timeout=timeout)
        sr = ScheduleResult(
            entry=entry,
            result=batch[0],
            scheduled_at=scheduled_at,
            started_at=started_at,
        )
        results.append(sr)
        if on_result:
            on_result(sr)
    return results
