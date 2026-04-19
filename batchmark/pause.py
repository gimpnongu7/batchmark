from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
import time

from batchmark.runner import CommandResult


@dataclass
class PauseConfig:
    after_every: int = 0          # pause after every N commands (0 = disabled)
    pause_seconds: float = 1.0    # how long to pause
    after_commands: List[str] = field(default_factory=list)  # pause after specific commands


@dataclass
class PauseState:
    count: int = 0
    total_paused: float = 0.0
    pause_count: int = 0

    def record_pause(self, seconds: float) -> None:
        self.total_paused += seconds
        self.pause_count += 1


def parse_pause_config(raw: dict) -> PauseConfig:
    return PauseConfig(
        after_every=int(raw.get("after_every", 0)),
        pause_seconds=float(raw.get("pause_seconds", 1.0)),
        after_commands=list(raw.get("after_commands", [])),
    )


def _should_pause(cfg: PauseConfig, state: PauseState, result: CommandResult) -> bool:
    if result.command in cfg.after_commands:
        return True
    if cfg.after_every > 0 and state.count % cfg.after_every == 0:
        return True
    return False


def run_with_pauses(
    results: List[CommandResult],
    cfg: PauseConfig,
    _sleep=time.sleep,
) -> tuple[List[CommandResult], PauseState]:
    state = PauseState()
    out: List[CommandResult] = []
    for result in results:
        out.append(result)
        state.count += 1
        if _should_pause(cfg, state, result):
            _sleep(cfg.pause_seconds)
            state.record_pause(cfg.pause_seconds)
    return out, state
