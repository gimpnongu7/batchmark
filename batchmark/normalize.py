from dataclasses import dataclass
from typing import List, Optional
from batchmark.runner import CommandResult


@dataclass
class NormalizeConfig:
    method: str = "min-max"  # "min-max" or "z-score"
    floor: float = 0.0
    ceiling: float = 1.0


def _min_max(value: float, mn: float, mx: float, floor: float, ceiling: float) -> float:
    if mx == mn:
        return floor
    normalized = (value - mn) / (mx - mn)
    return floor + normalized * (ceiling - floor)


def _z_score(value: float, mean: float, std: float) -> float:
    if std == 0.0:
        return 0.0
    return (value - mean) / std


def normalize_durations(
    results: List[CommandResult],
    cfg: Optional[NormalizeConfig] = None,
) -> List[dict]:
    """Return list of dicts with original result fields plus 'normalized_duration'."""
    if cfg is None:
        cfg = NormalizeConfig()

    durations = [r.duration for r in results]
    if not durations:
        return []

    if cfg.method == "z-score":
        mean = sum(durations) / len(durations)
        variance = sum((d - mean) ** 2 for d in durations) / len(durations)
        std = variance ** 0.5
        scores = [_z_score(d, mean, std) for d in durations]
    else:
        mn, mx = min(durations), max(durations)
        scores = [_min_max(d, mn, mx, cfg.floor, cfg.ceiling) for d in durations]

    output = []
    for result, score in zip(results, scores):
        output.append({
            "command": result.command,
            "status": result.status,
            "duration": result.duration,
            "normalized_duration": round(score, 6),
            "returncode": result.returncode,
        })
    return output


def parse_normalize_config(raw: dict) -> NormalizeConfig:
    section = raw.get("normalize", {})
    return NormalizeConfig(
        method=section.get("method", "min-max"),
        floor=float(section.get("floor", 0.0)),
        ceiling=float(section.get("ceiling", 1.0)),
    )
