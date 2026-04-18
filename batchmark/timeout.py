"""Per-command and global timeout configuration and enforcement."""
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class TimeoutConfig:
    default: float = 30.0
    per_command: Dict[str, float] = field(default_factory=dict)
    global_budget: Optional[float] = None


def resolve_timeout(config: TimeoutConfig, command: str) -> float:
    """Return the effective timeout for a given command."""
    return config.per_command.get(command, config.default)


def parse_timeout_config(raw: dict) -> TimeoutConfig:
    """Build a TimeoutConfig from a raw config dict (e.g. loaded from YAML/JSON)."""
    timeout_section = raw.get("timeouts", {})
    default = float(timeout_section.get("default", 30.0))
    per_command = {k: float(v) for k, v in timeout_section.get("per_command", {}).items()}
    global_budget = timeout_section.get("global_budget")
    if global_budget is not None:
        global_budget = float(global_budget)
    return TimeoutConfig(default=default, per_command=per_command, global_budget=global_budget)


def budget_remaining(budget: Optional[float], elapsed: float) -> Optional[float]:
    """Return remaining global budget, or None if no budget is set."""
    if budget is None:
        return None
    remaining = budget - elapsed
    return max(remaining, 0.0)


def effective_timeout(cmd_timeout: float, remaining: Optional[float]) -> float:
    """Clamp command timeout to the remaining global budget if applicable."""
    if remaining is None:
        return cmd_timeout
    return min(cmd_timeout, remaining)
