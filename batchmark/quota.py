from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from batchmark.runner import CommandResult


@dataclass
class QuotaConfig:
    max_failures: Optional[int] = None
    max_duration: Optional[float] = None  # total wall-clock seconds
    max_commands: Optional[int] = None


@dataclass
class QuotaState:
    config: QuotaConfig
    failures: int = 0
    total_duration: float = 0.0
    commands_run: int = 0
    stopped_reason: Optional[str] = None

    def record(self, result: CommandResult) -> None:
        self.commands_run += 1
        self.total_duration += result.duration
        if result.status != "success":
            self.failures += 1

    def exceeded(self) -> Optional[str]:
        cfg = self.config
        if cfg.max_failures is not None and self.failures >= cfg.max_failures:
            return f"failure quota reached ({self.failures}/{cfg.max_failures})"
        if cfg.max_duration is not None and self.total_duration >= cfg.max_duration:
            return f"duration quota reached ({self.total_duration:.2f}s/{cfg.max_duration}s)"
        if cfg.max_commands is not None and self.commands_run >= cfg.max_commands:
            return f"command quota reached ({self.commands_run}/{cfg.max_commands})"
        return None


def parse_quota_config(data: dict) -> QuotaConfig:
    return QuotaConfig(
        max_failures=data.get("max_failures"),
        max_duration=data.get("max_duration"),
        max_commands=data.get("max_commands"),
    )


def run_with_quota(
    commands: List[str],
    config: QuotaConfig,
    run_fn,
) -> tuple[List[CommandResult], QuotaState]:
    state = QuotaState(config=config)
    results: List[CommandResult] = []
    for cmd in commands:
        result = run_fn(cmd)
        state.record(result)
        results.append(result)
        reason = state.exceeded()
        if reason:
            state.stopped_reason = reason
            break
    return results, state
