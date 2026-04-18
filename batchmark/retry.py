"""Retry logic for flaky commands."""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import List, Optional
from batchmark.runner import CommandResult, run_command


@dataclass
class RetryConfig:
    max_attempts: int = 3
    delay: float = 0.5
    retry_on_timeout: bool = True
    retry_on_failure: bool = True


@dataclass
class RetryResult:
    final: CommandResult
    attempts: List[CommandResult] = field(default_factory=list)
    succeeded_on: Optional[int] = None

    @property
    def total_attempts(self) -> int:
        return len(self.attempts)


def should_retry(result: CommandResult, cfg: RetryConfig) -> bool:
    if result.timed_out and cfg.retry_on_timeout:
        return True
    if not result.timed_out and result.returncode != 0 and cfg.retry_on_failure:
        return True
    return False


def run_with_retry(
    command: str,
    timeout: Optional[float] = None,
    cfg: Optional[RetryConfig] = None,
) -> RetryResult:
    if cfg is None:
        cfg = RetryConfig()

    attempts: List[CommandResult] = []

    for attempt in range(1, cfg.max_attempts + 1):
        result = run_command(command, timeout=timeout)
        attempts.append(result)

        if result.returncode == 0 and not result.timed_out:
            return RetryResult(final=result, attempts=attempts, succeeded_on=attempt)

        if attempt < cfg.max_attempts and should_retry(result, cfg):
            time.sleep(cfg.delay)
        else:
            break

    return RetryResult(final=attempts[-1], attempts=attempts, succeeded_on=None)
