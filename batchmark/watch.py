"""Watch mode: re-run a batch config on file change or interval."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional

from batchmark.config import load_config
from batchmark.runner import CommandResult, run_batch


@dataclass
class WatchOptions:
    config_path: str
    interval: float = 5.0
    max_runs: Optional[int] = None
    on_run: Optional[Callable[[int, List[CommandResult]], None]] = None


@dataclass
class WatchSummary:
    total_runs: int = 0
    run_timestamps: List[float] = field(default_factory=list)

    def record(self) -> None:
        self.total_runs += 1
        self.run_timestamps.append(time.time())


def _config_mtime(path: str) -> float:
    try:
        return Path(path).stat().st_mtime
    except FileNotFoundError:
        return 0.0


def watch(options: WatchOptions) -> WatchSummary:
    """Repeatedly load config and run batch, sleeping between runs."""
    summary = WatchSummary()
    last_mtime = None
    run_count = 0

    while True:
        current_mtime = _config_mtime(options.config_path)
        if last_mtime is None or current_mtime != last_mtime:
            last_mtime = current_mtime
            config = load_config(options.config_path)
            commands = config["commands"]
            timeout = config.get("timeout")
            results = run_batch(commands, timeout=timeout)
            summary.record()
            run_count += 1
            if options.on_run:
                options.on_run(run_count, results)

        if options.max_runs is not None and run_count >= options.max_runs:
            break

        time.sleep(options.interval)

    return summary
