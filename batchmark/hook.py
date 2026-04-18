"""Pre/post run hooks for batchmark."""
from __future__ import annotations
import subprocess
from dataclasses import dataclass, field
from typing import Callable, List, Optional
from batchmark.runner import CommandResult


@dataclass
class HookConfig:
    pre_batch: List[str] = field(default_factory=list)
    post_batch: List[str] = field(default_factory=list)
    pre_command: List[str] = field(default_factory=list)
    post_command: List[str] = field(default_factory=list)


@dataclass
class HookResult:
    hook: str
    returncode: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        return self.returncode == 0


def run_hook(cmd: str, timeout: Optional[float] = 30.0) -> HookResult:
    """Run a single hook shell command and return its result."""
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return HookResult(
            hook=cmd,
            returncode=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )
    except subprocess.TimeoutExpired:
        return HookResult(hook=cmd, returncode=-1, stdout="", stderr="timeout")


def run_hooks(
    hooks: List[str],
    on_failure: str = "warn",
    timeout: Optional[float] = 30.0,
) -> List[HookResult]:
    """Run a list of hook commands.

    on_failure: 'warn' | 'raise'
    """
    results = []
    for cmd in hooks:
        hr = run_hook(cmd, timeout=timeout)
        if not hr.success and on_failure == "raisef"Hook failed: {cmd!r} (rc={hr.returncode}) {hr.stderr}")
        results.append(hr)
    return results


def load_hook_config(raw: dict) -> HookConfig:
    """Build HookConfig from a config dict (e.g. parsed YAML/JSON)."""
    hooks = raw.get("hooks", {})
    return HookConfig(
        pre_batch=hooks.get("pre_batch", []),
        post_batch=hooks.get("post_batch", []),
        pre_command=hooks.get("pre_command", []),
        post_command=hooks.get("post_command", []),
    )
