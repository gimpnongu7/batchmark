from dataclasses import dataclass
from typing import List, Optional
from batchmark.runner import CommandResult
from batchmark.stats import compute_stats


@dataclass
class OutlierConfig:
    method: str = "iqr"  # "iqr" or "zscore"
    iqr_factor: float = 1.5
    zscore_threshold: float = 2.0
    include_failures: bool = False


@dataclass
class OutlierResult:
    result: CommandResult
    score: float
    reason: str


def _durations(results: List[CommandResult]) -> List[float]:
    return [r.duration for r in results]


def detect_outliers(
    results: List[CommandResult],
    config: Optional[OutlierConfig] = None,
) -> List[OutlierResult]:
    if config is None:
        config = OutlierConfig()

    candidates = results if config.include_failures else [r for r in results if r.returncode == 0]
    if len(candidates) < 3:
        return []

    stats = compute_stats(candidates)
    outliers: List[OutlierResult] = []

    if config.method == "iqr":
        durations = sorted(_durations(candidates))
        n = len(durations)
        q1 = durations[n // 4]
        q3 = durations[(3 * n) // 4]
        iqr = q3 - q1
        lo = q1 - config.iqr_factor * iqr
        hi = q3 + config.iqr_factor * iqr
        for r in candidates:
            if r.duration < lo or r.duration > hi:
                score = max(abs(r.duration - q1), abs(r.duration - q3)) / (iqr or 1.0)
                reason = f"duration {r.duration:.3f}s outside IQR fence [{lo:.3f}, {hi:.3f}]"
                outliers.append(OutlierResult(result=r, score=round(score, 4), reason=reason))
    else:
        mean = stats.mean
        std = stats.stdev if stats.stdev else 0.0
        if std == 0:
            return []
        for r in candidates:
            z = abs(r.duration - mean) / std
            if z > config.zscore_threshold:
                reason = f"z-score {z:.3f} exceeds threshold {config.zscore_threshold}"
                outliers.append(OutlierResult(result=r, score=round(z, 4), reason=reason))

    return sorted(outliers, key=lambda o: o.score, reverse=True)


def parse_outlier_config(raw: dict) -> OutlierConfig:
    return OutlierConfig(
        method=raw.get("method", "iqr"),
        iqr_factor=float(raw.get("iqr_factor", 1.5)),
        zscore_threshold=float(raw.get("zscore_threshold", 2.0)),
        include_failures=bool(raw.get("include_failures", False)),
    )
