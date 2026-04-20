"""sweep.py — run a command across a range of parameter values and collect results."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, List

from batchmark.runner import CommandResult


@dataclass
class SweepConfig:
    param_name: str
    values: List[Any]
    command_template: str  # e.g. "sleep {n}"
    timeout: float = 30.0


@dataclass
class SweepResult:
    param_value: Any
    result: CommandResult

    @property
    def command(self) -> str:
        return self.result.command

    @property
    def duration(self) -> float:
        return self.result.duration

    @property
    def status(self) -> str:
        return self.result.status


def render_command(template: str, param_name: str, value: Any) -> str:
    """Substitute {param_name} in template with value."""
    return template.replace(f"{{{param_name}}}", str(value))


def run_sweep(
    config: SweepConfig,
    run_fn: Callable[[str, float], CommandResult],
) -> List[SweepResult]:
    """Run the command template for each value in the sweep."""
    results: List[SweepResult] = []
    for value in config.values:
        cmd = render_command(config.command_template, config.param_name, value)
        result = run_fn(cmd, config.timeout)
        results.append(SweepResult(param_value=value, result=result))
    return results


def parse_sweep_config(data: dict) -> SweepConfig:
    """Parse a sweep config from a plain dict (e.g. loaded from YAML/JSON)."""
    return SweepConfig(
        param_name=data["param_name"],
        values=data["values"],
        command_template=data["command_template"],
        timeout=float(data.get("timeout", 30.0)),
    )
