"""Notification hooks for batch run completion."""
from dataclasses import dataclass, field
from typing import Optional, Callable
from batchmark.stats import BatchStats


@dataclass
class NotifyConfig:
    on_complete: bool = True
    on_failure: bool = True
    min_failures: int = 1
    handler: Optional[Callable[[str, "NotifyEvent"], None]] = field(default=None, repr=False)


@dataclass
class NotifyEvent:
    kind: str  # 'complete' or 'failure'
    stats: BatchStats
    message: str


def _default_handler(label: str, event: NotifyEvent) -> None:
    print(f"[batchmark notify] [{label}] {event.message}")


def build_message(kind: str, stats: BatchStats) -> str:
    if kind == "failure":
        return (
            f"Batch finished with {stats.failed} failure(s) "
            f"out of {stats.total} commands "
            f"(total time: {stats.total_duration:.3f}s)"
        )
    return (
        f"Batch complete: {stats.total} commands, "
        f"{stats.passed} passed, {stats.failed} failed, "
        f"avg {stats.avg_duration:.3f}s"
    )


def should_notify(config: NotifyConfig, stats: BatchStats, kind: str) -> bool:
    if kind == "complete" and config.on_complete:
        return True
    if kind == "failure" and config.on_failure and stats.failed >= config.min_failures:
        return True
    return False


def notify(config: NotifyConfig, stats: BatchStats, label: str = "run") -> list[NotifyEvent]:
    handler = config.handler or _default_handler
    fired: list[NotifyEvent] = []
    for kind in ("failure", "complete"):
        if should_notify(config, stats, kind):
            msg = build_message(kind, stats)
            event = NotifyEvent(kind=kind, stats=stats, message=msg)
            handler(label, event)
            fired.append(event)
    return fired
