from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from batchmark.runner import CommandResult


@dataclass
class FenceConfig:
    min_duration: Optional[float] = None
    max_duration: Optional[float] = None
    allow_statuses: Optional[List[str]] = None  # None means all allowed
    deny_statuses: Optional[List[str]] = None


@dataclass
class FenceResult:
    result: CommandResult
    allowed: bool
    reason: Optional[str]

    @property
    def command(self) -> str:
        return self.result.command

    @property
    def duration(self) -> float:
        return self.result.duration

    @property
    def status(self) -> str:
        return self.result.status


def parse_fence_config(raw: dict) -> FenceConfig:
    return FenceConfig(
        min_duration=raw.get("min_duration"),
        max_duration=raw.get("max_duration"),
        allow_statuses=raw.get("allow_statuses"),
        deny_statuses=raw.get("deny_statuses"),
    )


def _check(result: CommandResult, cfg: FenceConfig) -> Optional[str]:
    if cfg.min_duration is not None and result.duration < cfg.min_duration:
        return f"duration {result.duration:.3f}s below min {cfg.min_duration:.3f}s"
    if cfg.max_duration is not None and result.duration > cfg.max_duration:
        return f"duration {result.duration:.3f}s above max {cfg.max_duration:.3f}s"
    if cfg.deny_statuses and result.status in cfg.deny_statuses:
        return f"status '{result.status}' is denied"
    if cfg.allow_statuses is not None and result.status not in cfg.allow_statuses:
        return f"status '{result.status}' not in allowed list"
    return None


def apply_fence(
    results: List[CommandResult], cfg: FenceConfig
) -> List[FenceResult]:
    out = []
    for r in results:
        reason = _check(r, cfg)
        out.append(FenceResult(result=r, allowed=reason is None, reason=reason))
    return out


def fence_summary(fenced: List[FenceResult]) -> dict:
    allowed = [f for f in fenced if f.allowed]
    blocked = [f for f in fenced if not f.allowed]
    return {
        "total": len(fenced),
        "allowed": len(allowed),
        "blocked": len(blocked),
    }
