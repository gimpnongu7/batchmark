"""Checkpoint support: save/resume batch run progress."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import List, Optional

from batchmark.runner import CommandResult


@dataclass
class CheckpointConfig:
    path: str
    resume: bool = True
    auto_save: bool = True


def _result_to_dict(r: CommandResult) -> dict:
    return {
        "command": r.command,
        "returncode": r.returncode,
        "stdout": r.stdout,
        "stderr": r.stderr,
        "duration": r.duration,
        "timed_out": r.timed_out,
    }


def _dict_to_result(d: dict) -> CommandResult:
    return CommandResult(
        command=d["command"],
        returncode=d["returncode"],
        stdout=d["stdout"],
        stderr=d["stderr"],
        duration=d["duration"],
        timed_out=d["timed_out"],
    )


def save_checkpoint(path: str, results: List[CommandResult]) -> None:
    data = [_result_to_dict(r) for r in results]
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_checkpoint(path: str) -> Optional[List[CommandResult]]:
    if not os.path.exists(path):
        return None
    with open(path) as f:
        data = json.load(f)
    return [_dict_to_result(d) for d in data]


def completed_commands(results: List[CommandResult]) -> set:
    return {r.command for r in results}


def filter_remaining(commands: List[str], done: set) -> List[str]:
    return [c for c in commands if c not in done]
