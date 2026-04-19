"""Bucket results into duration-based ranges."""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from batchmark.runner import CommandResult


@dataclass
class BucketConfig:
    boundaries: List[float]  # e.g. [0.5, 1.0, 2.0] creates 4 buckets
    labels: Optional[List[str]] = None  # optional names per bucket

    def __post_init__(self):
        self.boundaries = sorted(self.boundaries)
        n = len(self.boundaries) + 1
        if self.labels is None:
            self.labels = _default_labels(self.boundaries)
        if len(self.labels) != n:
            raise ValueError(f"Expected {n} labels for {len(self.boundaries)} boundaries")


@dataclass
class BucketResult:
    label: str
    lower: Optional[float]  # None means -inf
    upper: Optional[float]  # None means +inf
    results: List[CommandResult] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.results)

    @property
    def mean_duration(self) -> Optional[float]:
        if not self.results:
            return None
        return sum(r.duration for r in self.results) / len(self.results)


def _default_labels(boundaries: List[float]) -> List[str]:
    labels = []
    prev = None
    for b in boundaries:
        lo = f"{prev}" if prev is not None else "-inf"
        labels.append(f"[{lo}, {b})")
        prev = b
    labels.append(f"[{prev}, +inf)")
    return labels


def bucket_results(results: List[CommandResult], cfg: BucketConfig) -> List[BucketResult]:
    buckets = []
    bounds = [None] + cfg.boundaries + [None]
    for i, label in enumerate(cfg.labels):
        buckets.append(BucketResult(label=label, lower=bounds[i], upper=bounds[i + 1]))

    for r in results:
        for i, b in enumerate(buckets):
            lo = b.lower if b.lower is not None else float("-inf")
            hi = b.upper if b.upper is not None else float("inf")
            if lo <= r.duration < hi:
                b.results.append(r)
                break
    return buckets


def parse_bucket_config(data: dict) -> BucketConfig:
    boundaries = data.get("boundaries", [])
    labels = data.get("labels", None)
    return BucketConfig(boundaries=boundaries, labels=labels)
