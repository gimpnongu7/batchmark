"""Sampling utilities for selecting subsets of results."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Optional

from batchmark.runner import CommandResult


@dataclass
class SampleConfig:
    n: Optional[int] = None
    fraction: Optional[float] = None
    seed: Optional[int] = None
    strategy: str = "random"  # random | head | tail | every_nth
    nth: int = 1


def parse_sample_config(data: dict) -> SampleConfig:
    return SampleConfig(
        n=data.get("n"),
        fraction=data.get("fraction"),
        seed=data.get("seed"),
        strategy=data.get("strategy", "random"),
        nth=data.get("nth", 1),
    )


def _resolve_n(cfg: SampleConfig, total: int) -> int:
    if cfg.n is not None:
        return min(cfg.n, total)
    if cfg.fraction is not None:
        return max(1, int(total * cfg.fraction))
    return total


def sample_results(
    results: List[CommandResult], cfg: SampleConfig
) -> List[CommandResult]:
    if not results:
        return []

    strategy = cfg.strategy
    total = len(results)

    if strategy == "head":
        n = _resolve_n(cfg, total)
        return results[:n]

    if strategy == "tail":
        n = _resolve_n(cfg, total)
        return results[total - n:]

    if strategy == "every_nth":
        step = max(1, cfg.nth)
        return results[::step]

    # default: random
    n = _resolve_n(cfg, total)
    rng = random.Random(cfg.seed)
    return rng.sample(results, n)
