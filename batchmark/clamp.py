from dataclasses import dataclass
from typing import Optional
from batchmark.runner import CommandResult


@dataclass
class ClampConfig:
    min_duration: Optional[float] = None
    max_duration: Optional[float] = None


def parse_clamp_config(raw: dict) -> ClampConfig:
    clamp = raw.get("clamp", {})
    return ClampConfig(
        min_duration=clamp.get("min_duration"),
        max_duration=clamp.get("max_duration"),
    )


def clamp_duration(value: float, cfg: ClampConfig) -> float:
    if cfg.min_duration is not None:
        value = max(value, cfg.min_duration)
    if cfg.max_duration is not None:
        value = min(value, cfg.max_duration)
    return value


def clamp_results(
    results: list[CommandResult], cfg: ClampConfig
) -> list[CommandResult]:
    out = []
    for r in results:
        clamped = clamp_duration(r.duration, cfg)
        if clamped == r.duration:
            out.append(r)
        else:
            out.append(
                CommandResult(
                    command=r.command,
                    returncode=r.returncode,
                    stdout=r.stdout,
                    stderr=r.stderr,
                    duration=clamped,
                    timed_out=r.timed_out,
                )
            )
    return out
