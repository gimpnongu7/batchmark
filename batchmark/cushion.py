"""cushion.py — adaptive inter-command padding based on recent duration variance."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from batchmark.runner import CommandResult


@dataclass
class CushionConfig:
    base_seconds: float = 0.0          # minimum pause between commands
    variance_factor: float = 0.1       # extra seconds per unit of std-dev
    window: int = 5                    # how many recent results to consider
    max_seconds: float = 10.0          # hard cap on any single cushion
    enabled: bool = True


@dataclass
class CushionState:
    config: CushionConfig
    _recent: List[float] = field(default_factory=list, repr=False)
    total_paused: float = 0.0
    pause_count: int = 0

    def record(self, result: CommandResult) -> None:
        self._recent.append(result.duration)
        if len(self._recent) > self.config.window:
            self._recent.pop(0)

    def _stddev(self) -> float:
        if len(self._recent) < 2:
            return 0.0
        mean = sum(self._recent) / len(self._recent)
        variance = sum((x - mean) ** 2 for x in self._recent) / len(self._recent)
        return variance ** 0.5

    def cushion_seconds(self) -> float:
        if not self.config.enabled:
            return 0.0
        extra = self._stddev() * self.config.variance_factor
        total = self.config.base_seconds + extra
        return min(total, self.config.max_seconds)


def parse_cushion_config(raw: dict) -> CushionConfig:
    c = raw.get("cushion", {})
    return CushionConfig(
        base_seconds=float(c.get("base_seconds", 0.0)),
        variance_factor=float(c.get("variance_factor", 0.1)),
        window=int(c.get("window", 5)),
        max_seconds=float(c.get("max_seconds", 10.0)),
        enabled=bool(c.get("enabled", True)),
    )


def run_cushioned(
    commands: List[str],
    run_fn: Callable[[str], CommandResult],
    config: Optional[CushionConfig] = None,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> List[CommandResult]:
    if config is None:
        config = CushionConfig()
    state = CushionState(config=config)
    results: List[CommandResult] = []
    for i, cmd in enumerate(commands):
        if i > 0:
            delay = state.cushion_seconds()
            if delay > 0:
                sleep_fn(delay)
                state.total_paused += delay
                state.pause_count += 1
        result = run_fn(cmd)
        state.record(result)
        results.append(result)
    return results
