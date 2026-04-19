"""Throttle: limit concurrency and add inter-command delays."""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional
from batchmark.runner import CommandResult


@dataclass
class ThrottleConfig:
    max_concurrency: int = 1        # currently sequential; >1 reserved
    inter_command_delay: float = 0.0  # seconds between commands
    burst: int = 0                  # allow N commands before delaying


def parse_throttle_config(raw: dict) -> ThrottleConfig:
    return ThrottleConfig(
        max_concurrency=int(raw.get("max_concurrency", 1)),
        inter_command_delay=float(raw.get("inter_command_delay", 0.0)),
        burst=int(raw.get("burst", 0)),
    )


def _should_delay(index: int, burst: int) -> bool:
    """Return True if a delay should be inserted before command at *index*."""
    if index == 0:
        return False
    if burst <= 0:
        return True
    return index % burst == 0


def run_throttled(
    commands: List[str],
    cfg: ThrottleConfig,
    run_fn: Callable[[str], CommandResult],
    sleep_fn: Callable[[float], None] = time.sleep,
) -> List[CommandResult]:
    """Run *commands* sequentially, honouring throttle settings."""
    results: List[CommandResult] = []
    for i, cmd in enumerate(commands):
        if cfg.inter_command_delay > 0 and _should_delay(i, cfg.burst):
            sleep_fn(cfg.inter_command_delay)
        results.append(run_fn(cmd))
    return results
