"""Result caching — store and retrieve batch run results by key."""
from __future__ import annotations

import json
import os
import hashlib
from dataclasses import asdict
from typing import Optional

from batchmark.runner import CommandResult


DEFAULT_CACHE_DIR = ".batchmark_cache"


def _cache_key(commands: list[str]) -> str:
    payload = json.dumps(sorted(commands), separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


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


def save_cache(commands: list[str], results: list[CommandResult], cache_dir: str = DEFAULT_CACHE_DIR) -> str:
    os.makedirs(cache_dir, exist_ok=True)
    key = _cache_key(commands)
    path = os.path.join(cache_dir, f"{key}.json")
    data = [_result_to_dict(r) for r in results]
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return path


def load_cache(commands: list[str], cache_dir: str = DEFAULT_CACHE_DIR) -> Optional[list[CommandResult]]:
    key = _cache_key(commands)
    path = os.path.join(cache_dir, f"{key}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        data = json.load(f)
    return [_dict_to_result(d) for d in data]


def clear_cache(cache_dir: str = DEFAULT_CACHE_DIR) -> int:
    if not os.path.isdir(cache_dir):
        return 0
    removed = 0
    for fname in os.listdir(cache_dir):
        if fname.endswith(".json"):
            os.remove(os.path.join(cache_dir, fname))
            removed += 1
    return removed
