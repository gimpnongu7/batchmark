"""Run a batch multiple times and aggregate results across runs."""
from dataclasses import dataclass, field
from typing import List, Callable, Optional
from batchmark.runner import CommandResult, run_batch


@dataclass
class RepeatConfig:
    times: int = 3
    delay: float = 0.0  # seconds between runs
    stop_on_error: bool = False


@dataclass
class RepeatSummary:
    command: str
    runs: List[CommandResult] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.runs if r.status == "success")

    @property
    def failure_count(self) -> int:
        return len(self.runs) - self.success_count

    @property
    def durations(self) -> List[float]:
        return [r.duration for r in self.runs]

    @property
    def mean_duration(self) -> float:
        d = self.durations
        return sum(d) / len(d) if d else 0.0

    @property
    def min_duration(self) -> float:
        return min(self.durations) if self.durations else 0.0

    @property
    def max_duration(self) -> float:
        return max(self.durations) if self.durations else 0.0


def repeat_batch(
    commands: List[str],
    config: RepeatConfig,
    timeout: Optional[float] = None,
    on_run: Optional[Callable[[int, List[CommandResult]], None]] = None,
) -> List[RepeatSummary]:
    import time

    summaries = {cmd: RepeatSummary(command=cmd) for cmd in commands}

    for i in range(config.times):
        results = run_batch(commands, timeout=timeout)
        for r in results:
            summaries[r.command].runs.append(r)
        if on_run:
            on_run(i + 1, results)
        if config.stop_on_error and any(r.status != "success" for r in results):
            break
        if config.delay > 0 and i < config.times - 1:
            time.sleep(config.delay)

    return list(summaries.values())


def summaries_to_dict(summaries: List[RepeatSummary]) -> List[dict]:
    return [
        {
            "command": s.command,
            "runs": len(s.runs),
            "success": s.success_count,
            "failure": s.failure_count,
            "mean_duration": round(s.mean_duration, 4),
            "min_duration": round(s.min_duration, 4),
            "max_duration": round(s.max_duration, 4),
        }
        for s in summaries
    ]
