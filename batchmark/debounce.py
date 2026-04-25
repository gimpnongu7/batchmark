from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from batchmark.runner import CommandResult


@dataclass
class DebounceConfig:
    window: float = 0.5  # seconds — suppress duplicate commands within this window
    key: str = "command"  # field to deduplicate on: 'command' or 'status'
    keep: str = "last"  # 'first' or 'last' result within each window


@dataclass
class DebounceState:
    config: DebounceConfig
    _buckets: dict = field(default_factory=dict)  # key -> list of results

    def record(self, result: CommandResult) -> None:
        k = _extract_key(result, self.config.key)
        self._buckets.setdefault(k, []).append(result)

    def flush(self) -> List[CommandResult]:
        out: List[CommandResult] = []
        for key, group in self._buckets.items():
            chosen = _pick(group, self.config.keep, self.config.window)
            out.extend(chosen)
        return out


def _extract_key(result: CommandResult, key: str) -> str:
    if key == "status":
        return result.status
    return result.command


def _pick(
    group: List[CommandResult], keep: str, window: float
) -> List[CommandResult]:
    """Within each time-window bucket, keep only first or last."""
    if not group:
        return []
    # sort by start_time for determinism
    sorted_group = sorted(group, key=lambda r: r.start_time)
    buckets: List[List[CommandResult]] = []
    current: List[CommandResult] = [sorted_group[0]]
    for r in sorted_group[1:]:
        if r.start_time - current[0].start_time <= window:
            current.append(r)
        else:
            buckets.append(current)
            current = [r]
    buckets.append(current)

    out: List[CommandResult] = []
    for b in buckets:
        out.append(b[-1] if keep == "last" else b[0])
    return out


def debounce_results(
    results: List[CommandResult], config: Optional[DebounceConfig] = None
) -> List[CommandResult]:
    cfg = config or DebounceConfig()
    state = DebounceState(config=cfg)
    for r in results:
        state.record(r)
    return state.flush()


def parse_debounce_config(raw: dict) -> DebounceConfig:
    return DebounceConfig(
        window=float(raw.get("window", 0.5)),
        key=str(raw.get("key", "command")),
        keep=str(raw.get("keep", "last")),
    )
