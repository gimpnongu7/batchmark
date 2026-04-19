"""Sliding window analysis over batches of CommandResults."""
from dataclasses import dataclass, field
from typing import List, Optional
from batchmark.runner import CommandResult


@dataclass
class WindowConfig:
    size: int = 5
    step: int = 1
    min_fill: float = 1.0  # fraction of window that must be filled (0.0-1.0)


@dataclass
class WindowSlice:
    index: int
    results: List[CommandResult]
    mean_duration: float
    success_rate: float
    commands: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.commands = [r.command for r in self.results]


def _mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def sliding_windows(results: List[CommandResult], cfg: Optional[WindowConfig] = None) -> List[WindowSlice]:
    if cfg is None:
        cfg = WindowConfig()
    slices = []
    n = len(results)
    min_count = max(1, int(cfg.size * cfg.min_fill))
    i = 0
    idx = 0
    while i < n:
        window = results[i:i + cfg.size]
        if len(window) < min_count:
            break
        durations = [r.duration for r in window]
        successes = sum(1 for r in window if r.returncode == 0)
        slices.append(WindowSlice(
            index=idx,
            results=window,
            mean_duration=_mean(durations),
            success_rate=successes / len(window),
        ))
        i += cfg.step
        idx += 1
    return slices


def format_window_table(slices: List[WindowSlice]) -> str:
    if not slices:
        return "No window data."
    header = f"{'Window':>8}  {'Size':>6}  {'Mean(s)':>10}  {'Success%':>10}"
    sep = "-" * len(header)
    rows = [header, sep]
    for s in slices:
        rows.append(
            f"{s.index:>8}  {len(s.results):>6}  {s.mean_duration:>10.4f}  {s.success_rate * 100:>9.1f}%"
        )
    return "\n".join(rows)


def parse_window_config(data: dict) -> WindowConfig:
    w = data.get("window", {})
    return WindowConfig(
        size=int(w.get("size", 5)),
        step=int(w.get("step", 1)),
        min_fill=float(w.get("min_fill", 1.0)),
    )
