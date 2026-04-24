"""Stagger command execution by inserting variable delays between runs."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from batchmark.runner import CommandResult


@dataclass
class StaggerConfig:
    delay: float = 0.0          # base delay in seconds between commands
    step: float = 0.0           # additional delay added per command index
    max_delay: Optional[float] = None  # cap on total delay
    jitter: float = 0.0         # random jitter fraction (0–1) applied to delay


@dataclass
class StaggerState:
    config: StaggerConfig
    _index: int = field(default=0, init=False)
    total_stagger_time: float = field(default=0.0, init=False)

    def next_delay(self, rng: Callable[[], float] = None) -> float:
        """Return the delay for the current command and advance the index."""
        base = self.config.delay + self.config.step * self._index
        if self.config.max_delay is not None:
            base = min(base, self.config.max_delay)
        if self.config.jitter > 0.0 and rng is not None:
            base = base * (1.0 + self.config.jitter * (rng() * 2.0 - 1.0))
            base = max(0.0, base)
        self._index += 1
        return base


def parse_stagger_config(raw: dict) -> StaggerConfig:
    return StaggerConfig(
        delay=float(raw.get("delay", 0.0)),
        step=float(raw.get("step", 0.0)),
        max_delay=float(raw["max_delay"]) if "max_delay" in raw else None,
        jitter=float(raw.get("jitter", 0.0)),
    )


def run_staggered(
    commands: List[str],
    run_fn: Callable[[str], CommandResult],
    config: StaggerConfig,
    sleep_fn: Callable[[float], None] = time.sleep,
    rng: Callable[[], float] = None,
) -> List[CommandResult]:
    """Run each command with a staggered delay applied before execution."""
    state = StaggerState(config=config)
    results: List[CommandResult] = []
    for cmd in commands:
        delay = state.next_delay(rng=rng)
        if delay > 0.0:
            sleep_fn(delay)
            state.total_stagger_time += delay
        results.append(run_fn(cmd))
    return results
