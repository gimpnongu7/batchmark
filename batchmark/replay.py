"""Replay a previous batch run from saved results, optionally re-running failed commands."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from batchmark.runner import CommandResult


@dataclass
class ReplayConfig:
    rerun_failed: bool = True
    rerun_timeout: bool = True
    max_replays: Optional[int] = None


@dataclass
class ReplayResult:
    original: CommandResult
    replayed: Optional[CommandResult] = None
    was_replayed: bool = False

    @property
    def final(self) -> CommandResult:
        return self.replayed if self.was_replayed and self.replayed is not None else self.original


def _should_replay(result: CommandResult, cfg: ReplayConfig) -> bool:
    if cfg.rerun_failed and result.status == "failure":
        return True
    if cfg.rerun_timeout and result.status == "timeout":
        return True
    return False


def replay_results(
    results: List[CommandResult],
    cfg: ReplayConfig,
    run_fn: Callable[[str], CommandResult],
) -> List[ReplayResult]:
    """Replay commands from a prior run according to cfg."""
    replayed: List[ReplayResult] = []
    replay_count = 0

    for r in results:
        if _should_replay(r, cfg):
            if cfg.max_replays is None or replay_count < cfg.max_replays:
                new_result = run_fn(r.command)
                replayed.append(ReplayResult(original=r, replayed=new_result, was_replayed=True))
                replay_count += 1
                continue
        replayed.append(ReplayResult(original=r))

    return replayed


def parse_replay_config(data: dict) -> ReplayConfig:
    section = data.get("replay", {})
    return ReplayConfig(
        rerun_failed=section.get("rerun_failed", True),
        rerun_timeout=section.get("rerun_timeout", True),
        max_replays=section.get("max_replays", None),
    )
