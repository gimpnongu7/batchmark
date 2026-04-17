import subprocess
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CommandResult:
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    success: bool = field(init=False)

    def __post_init__(self):
        self.success = self.exit_code == 0


def run_command(command: str, timeout: Optional[float] = None) -> CommandResult:
    """Run a single shell command and return timing + result info."""
    start = time.perf_counter()
    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        duration = time.perf_counter() - start
        return CommandResult(
            command=command,
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            duration_seconds=round(duration, 6),
        )
    except subprocess.TimeoutExpired:
        duration = time.perf_counter() - start
        return CommandResult(
            command=command,
            exit_code=-1,
            stdout="",
            stderr=f"Command timed out after {timeout}s",
            duration_seconds=round(duration, 6),
        )


def run_batch(commands: list[str], timeout: Optional[float] = None) -> list[CommandResult]:
    """Run a list of commands sequentially and return all results."""
    return [run_command(cmd, timeout=timeout) for cmd in commands]
