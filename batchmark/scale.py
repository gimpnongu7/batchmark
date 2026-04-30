"""Scale command durations by a fixed multiplier or per-command factors."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from batchmark.runner import CommandResult


@dataclass
class ScaleConfig:
    factor: float = 1.0
    per_command: Dict[str, float] = None  # type: ignore[assignment]
    min_duration: float = 0.0

    def __post_init__(self) -> None:
        if self.per_command is None:
            self.per_command = {}
        if self.factor <= 0:
            raise ValueError(f"factor must be positive, got {self.factor}")
        if self.min_duration < 0:
            raise ValueError(f"min_duration must be >= 0, got {self.min_duration}")


@dataclass
class ScaledResult:
    result: CommandResult
    raw_duration: float
    scale_factor: float

    @property
    def command(self) -> str:
        return self.result.command

    @property
    def status(self) -> str:
        return self.result.status

    @property
    def duration(self) -> float:
        return self.result.duration


def parse_scale_config(data: dict) -> ScaleConfig:
    return ScaleConfig(
        factor=float(data.get("factor", 1.0)),
        per_command=dict(data.get("per_command", {})),
        min_duration=float(data.get("min_duration", 0.0)),
    )


def scale_results(
    results: List[CommandResult],
    config: Optional[ScaleConfig] = None,
) -> List[ScaledResult]:
    if config is None:
        config = ScaleConfig()

    scaled: List[ScaledResult] = []
    for r in results:
        factor = config.per_command.get(r.command, config.factor)
        raw = r.duration
        new_duration = max(config.min_duration, raw * factor)
        adjusted = CommandResult(
            command=r.command,
            returncode=r.returncode,
            stdout=r.stdout,
            stderr=r.stderr,
            duration=new_duration,
            status=r.status,
        )
        scaled.append(ScaledResult(result=adjusted, raw_duration=raw, scale_factor=factor))
    return scaled


def scale_summary(scaled: List[ScaledResult]) -> dict:
    if not scaled:
        return {"count": 0, "total_raw": 0.0, "total_scaled": 0.0}
    total_raw = sum(s.raw_duration for s in scaled)
    total_scaled = sum(s.duration for s in scaled)
    return {
        "count": len(scaled),
        "total_raw": round(total_raw, 6),
        "total_scaled": round(total_scaled, 6),
        "ratio": round(total_scaled / total_raw, 6) if total_raw else 1.0,
    }
