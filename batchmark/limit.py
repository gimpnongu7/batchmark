"""Concurrency and rate limiting utilities for batchmark."""
from __future__ import annotations

from dataclasses import dataclass, field
from threading import Semaphore
from typing import Callable, Iterable, List

from batchmark.runner import CommandResult, run_command


@dataclass
class LimitConfig:
    max_workers: int = 4
    rate_limit: int = 0  # max commands per second, 0 = unlimited


def _rate_delay(rate_limit: int) -> float:
    """Return per-command delay in seconds for a given rate limit."""
    if rate_limit <= 0:
        return 0.0
    return 1.0 / rate_limit


def run_limited(
    commands: List[str],
    config: LimitConfig,
    timeout: float | None = None,
    on_result: Callable[[CommandResult], None] | None = None,
) -> List[CommandResult]:
    """Run commands with concurrency and optional rate limiting."""
    import time
    from concurrent.futures import ThreadPoolExecutor, as_completed

    semaphore = Semaphore(config.max_workers)
    delay = _rate_delay(config.rate_limit)
    results: List[CommandResult] = [None] * len(commands)  # type: ignore

    def _run(index: int, cmd: str) -> tuple[int, CommandResult]:
        with semaphore:
            if delay:
                time.sleep(delay)
            result = run_command(cmd, timeout=timeout)
            return index, result

    with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
        futures = {executor.submit(_run, i, cmd): i for i, cmd in enumerate(commands)}
        for future in as_completed(futures):
            idx, result = future.result()
            results[idx] = result
            if on_result:
                on_result(result)

    return results
