"""Cooldown support: enforce a minimum gap between command executions."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from batchmark.runner import CommandResult


@dataclass
class CooldownConfig:
    """Configuration for inter-command cooldown."""
    seconds: float = 0.0          # minimum pause between commands
    after_failure: float = 0.0    # extra pause after a failed command
    after_timeout: float = 0.0    # extra pause after a timed-out command


@dataclass
class CooldownState:
    config: CooldownConfig
    _paused_total: float = field(default=0.0, init=False)
    _pause_count: int = field(default=0, init=False)

    @property
    def paused_total(self) -> float:
        return self._paused_total

    @property
    def pause_count(self) -> int:
        return self._pause_count

    def record_pause(self, duration: float) -> None:
        self._paused_total += duration
        self._pause_count += 1


def _cooldown_seconds(config: CooldownConfig, result: Optional[CommandResult]) -> float:
    """Return how long to wait after *result* (None means before the first command)."""
    if result is None:
        return 0.0
    extra = 0.0
    if result.status == "timeout":
        extra = config.after_timeout
    elif result.status == "failure":
        extra = config.after_failure
    return config.seconds + extra


def run_with_cooldown(
    commands: List[str],
    config: CooldownConfig,
    run_fn: Callable[[str], CommandResult],
    sleep_fn: Callable[[float], None] = time.sleep,
) -> tuple[List[CommandResult], CooldownState]:
    """Run *commands* with cooldown gaps; return results and state."""
    state = CooldownState(config=config)
    results: List[CommandResult] = []
    prev: Optional[CommandResult] = None

    for cmd in commands:
        wait = _cooldown_seconds(config, prev)
        if wait > 0:
            sleep_fn(wait)
            state.record_pause(wait)
        result = run_fn(cmd)
        results.append(result)
        prev = result

    return results, state


def parse_cooldown_config(raw: dict) -> CooldownConfig:
    """Build a CooldownConfig from a raw config dict."""
    cd = raw.get("cooldown", {})
    return CooldownConfig(
        seconds=float(cd.get("seconds", 0.0)),
        after_failure=float(cd.get("after_failure", 0.0)),
        after_timeout=float(cd.get("after_timeout", 0.0)),
    )
