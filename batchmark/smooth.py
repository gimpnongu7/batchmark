"""Smoothing module: apply rolling-average smoothing to command durations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from batchmark.runner import CommandResult


@dataclass
class SmoothedResult:
    result: CommandResult
    raw_duration: float
    smoothed_duration: float
    window_size: int

    @property
    def command(self) -> str:
        return self.result.command

    @property
    def status(self) -> str:
        return self.result.status


@dataclass
class SmoothConfig:
    window: int = 3
    per_command: bool = True


def parse_smooth_config(raw: dict) -> SmoothConfig:
    return SmoothConfig(
        window=int(raw.get("window", 3)),
        per_command=bool(raw.get("per_command", True)),
    )


def _rolling_means(values: List[float], window: int) -> List[float]:
    """Return rolling mean for each position; early positions use available data."""
    out: List[float] = []
    for i, _ in enumerate(values):
        start = max(0, i - window + 1)
        chunk = values[start : i + 1]
        out.append(sum(chunk) / len(chunk))
    return out


def smooth_results(
    results: List[CommandResult],
    config: Optional[SmoothConfig] = None,
) -> List[SmoothedResult]:
    if config is None:
        config = SmoothConfig()

    if config.per_command:
        from collections import defaultdict

        groups: dict = defaultdict(list)
        order: List[tuple] = []
        for idx, r in enumerate(results):
            groups[r.command].append((idx, r))
            order.append((r.command, len(groups[r.command]) - 1))

        smoothed_map: dict = {}
        for cmd, items in groups.items():
            durations = [r.duration for _, r in items]
            means = _rolling_means(durations, config.window)
            smoothed_map[cmd] = means

        out: List[SmoothedResult] = []
        cmd_cursor: dict = {}
        for r in results:
            pos = cmd_cursor.get(r.command, 0)
            cmd_cursor[r.command] = pos + 1
            out.append(
                SmoothedResult(
                    result=r,
                    raw_duration=r.duration,
                    smoothed_duration=round(smoothed_map[r.command][pos], 6),
                    window_size=config.window,
                )
            )
        return out
    else:
        durations = [r.duration for r in results]
        means = _rolling_means(durations, config.window)
        return [
            SmoothedResult(
                result=r,
                raw_duration=r.duration,
                smoothed_duration=round(m, 6),
                window_size=config.window,
            )
            for r, m in zip(results, means)
        ]
