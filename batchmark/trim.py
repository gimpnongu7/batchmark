"""Trim results list by slicing head/tail or dropping outliers."""
from dataclasses import dataclass
from typing import List, Optional
from batchmark.runner import CommandResult


@dataclass
class TrimConfig:
    head: Optional[int] = None   # keep first N
    tail: Optional[int] = None   # keep last N
    drop_fastest: int = 0
    drop_slowest: int = 0


def parse_trim_config(cfg: dict) -> TrimConfig:
    return TrimConfig(
        head=cfg.get("head"),
        tail=cfg.get("tail"),
        drop_fastest=int(cfg.get("drop_fastest", 0)),
        drop_slowest=int(cfg.get("drop_slowest", 0)),
    )


def trim_results(results: List[CommandResult], config: TrimConfig) -> List[CommandResult]:
    """Apply trim rules in order: drop outliers, then head/tail slice."""
    out = list(results)

    if config.drop_fastest or config.drop_slowest:
        sorted_by_dur = sorted(out, key=lambda r: r.duration)
        drop_f = config.drop_fastest
        drop_s = config.drop_slowest
        if drop_f + drop_s >= len(sorted_by_dur):
            return []
        trimmed_set = set(id(r) for r in sorted_by_dur[drop_f: len(sorted_by_dur) - drop_s if drop_s else None])
        out = [r for r in out if id(r) in trimmed_set]

    if config.head is not None:
        out = out[: config.head]
    elif config.tail is not None:
        out = out[-config.tail:] if config.tail else []

    return out
