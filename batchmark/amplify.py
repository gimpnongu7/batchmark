from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from batchmark.runner import CommandResult


@dataclass
class AmplifyConfig:
    factor: float = 1.0
    min_duration: Optional[float] = None
    max_duration: Optional[float] = None
    only_failures: bool = False


def parse_amplify_config(raw: dict) -> AmplifyConfig:
    factor = float(raw.get("factor", 1.0))
    if factor <= 0:
        raise ValueError(f"amplify factor must be positive, got {factor}")
    return AmplifyConfig(
        factor=factor,
        min_duration=raw.get("min_duration"),
        max_duration=raw.get("max_duration"),
        only_failures=bool(raw.get("only_failures", False)),
    )


@dataclass
class AmplifiedResult:
    result: CommandResult
    original_duration: float
    amplified_duration: float
    was_amplified: bool

    @property
    def command(self) -> str:
        return self.result.command

    @property
    def status(self) -> str:
        return self.result.status


def _should_amplify(result: CommandResult, cfg: AmplifyConfig) -> bool:
    if cfg.only_failures and result.status != "failure":
        return False
    if cfg.min_duration is not None and result.duration < cfg.min_duration:
        return False
    if cfg.max_duration is not None and result.duration > cfg.max_duration:
        return False
    return True


def amplify_results(
    results: List[CommandResult], cfg: AmplifyConfig
) -> List[AmplifiedResult]:
    out: List[AmplifiedResult] = []
    for r in results:
        original = r.duration
        if _should_amplify(r, cfg):
            amplified = original * cfg.factor
            was = True
        else:
            amplified = original
            was = False
        out.append(
            AmplifiedResult(
                result=r,
                original_duration=original,
                amplified_duration=amplified,
                was_amplified=was,
            )
        )
    return out


def amplify_summary(entries: List[AmplifiedResult]) -> dict:
    total = len(entries)
    amplified = sum(1 for e in entries if e.was_amplified)
    delta = sum(e.amplified_duration - e.original_duration for e in entries)
    return {
        "total": total,
        "amplified_count": amplified,
        "skipped_count": total - amplified,
        "total_duration_delta": round(delta, 6),
    }
