"""cadence.py — detect and report execution cadence (inter-arrival timing) across a batch run."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from batchmark.runner import CommandResult


@dataclass
class CadenceEntry:
    command: str
    duration: float
    gap: Optional[float]        # seconds since previous result finished
    cumulative: float           # seconds from batch start
    index: int

    @property
    def is_late(self) -> bool:
        """True when gap exceeds the configured threshold."""
        return self.gap is not None and self.gap > 0.0


@dataclass
class CadenceConfig:
    late_threshold: float = 0.5   # gap (s) considered "late"
    include_failed: bool = True


def parse_cadence_config(raw: dict) -> CadenceConfig:
    return CadenceConfig(
        late_threshold=float(raw.get("late_threshold", 0.5)),
        include_failed=bool(raw.get("include_failed", True)),
    )


def compute_cadence(
    results: Sequence[CommandResult],
    cfg: Optional[CadenceConfig] = None,
) -> List[CadenceEntry]:
    if cfg is None:
        cfg = CadenceConfig()

    filtered = [
        r for r in results
        if cfg.include_failed or r.status == "success"
    ]

    entries: List[CadenceEntry] = []
    cumulative = 0.0
    prev_end: Optional[float] = None

    for idx, result in enumerate(filtered):
        gap: Optional[float] = None
        if prev_end is not None:
            gap = max(0.0, cumulative - prev_end)

        entry = CadenceEntry(
            command=result.command,
            duration=result.duration,
            gap=gap,
            cumulative=cumulative,
            index=idx,
        )
        entries.append(entry)
        prev_end = cumulative + result.duration
        cumulative += result.duration

    return entries


def cadence_summary(entries: List[CadenceEntry]) -> dict:
    if not entries:
        return {"count": 0, "total_duration": 0.0, "mean_gap": None}
    gaps = [e.gap for e in entries if e.gap is not None]
    mean_gap = sum(gaps) / len(gaps) if gaps else None
    return {
        "count": len(entries),
        "total_duration": sum(e.duration for e in entries),
        "mean_gap": mean_gap,
    }
