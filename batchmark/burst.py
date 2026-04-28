from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from batchmark.runner import CommandResult


@dataclass
class BurstConfig:
    window: float = 1.0          # seconds to look back
    max_in_window: int = 3       # max commands allowed in window
    cooldown: float = 0.5        # seconds to sleep when limit hit
    enabled: bool = True


@dataclass
class BurstEntry:
    result: CommandResult
    window_count: int            # how many ran in the preceding window
    throttled: bool              # was a cooldown applied before this
    cooldown_applied: float      # actual seconds slept

    @property
    def command(self) -> str:
        return self.result.command

    @property
    def duration(self) -> float:
        return self.result.duration

    @property
    def status(self) -> str:
        return self.result.status


def parse_burst_config(raw: dict) -> BurstConfig:
    cfg = raw.get("burst", {})
    window = float(cfg.get("window", 1.0))
    max_in_window = int(cfg.get("max_in_window", 3))
    cooldown = float(cfg.get("cooldown", 0.5))
    enabled = bool(cfg.get("enabled", True))
    if window <= 0:
        raise ValueError("burst.window must be positive")
    if max_in_window < 1:
        raise ValueError("burst.max_in_window must be >= 1")
    if cooldown < 0:
        raise ValueError("burst.cooldown must be >= 0")
    return BurstConfig(window=window, max_in_window=max_in_window,
                       cooldown=cooldown, enabled=enabled)


def _count_in_window(timestamps: List[float], before: float, window: float) -> int:
    cutoff = before - window
    return sum(1 for t in timestamps if t >= cutoff)


def detect_bursts(
    results: List[CommandResult],
    cfg: Optional[BurstConfig] = None,
    *,
    _sleep_fn=None,
) -> List[BurstEntry]:
    """Replay results in order, recording which would have triggered a cooldown."""
    import time as _time

    if cfg is None:
        cfg = BurstConfig()

    sleep_fn = _sleep_fn if _sleep_fn is not None else _time.sleep
    entries: List[BurstEntry] = []
    timestamps: List[float] = []
    virtual_clock: float = 0.0

    for result in results:
        count = _count_in_window(timestamps, virtual_clock, cfg.window)
        throttled = cfg.enabled and count >= cfg.max_in_window
        slept = cfg.cooldown if throttled else 0.0
        if throttled:
            sleep_fn(slept)
            virtual_clock += slept
        timestamps.append(virtual_clock)
        virtual_clock += result.duration
        entries.append(BurstEntry(
            result=result,
            window_count=count,
            throttled=throttled,
            cooldown_applied=slept,
        ))
    return entries
