"""Config loading and validation for batchmark."""
import json
import os
from typing import Any

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


def load_config(path: str) -> dict[str, Any]:
    """Load a JSON or YAML config file and return its contents as a dict."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    ext = os.path.splitext(path)[1].lower()
    if ext == ".json":
        with open(path) as f:
            data = json.load(f)
    elif ext in (".yaml", ".yml"):
        if not _YAML_AVAILABLE:
            raise ImportError("PyYAML is required to load YAML configs: pip install pyyaml")
        with open(path) as f:
            data = yaml.safe_load(f)
    else:
        raise ValueError(f"Unsupported config format: {ext!r}. Use .json or .yaml")

    _validate_config(data)
    return data


def _validate_config(data: dict[str, Any]) -> None:
    """Raise ValueError if required fields are missing or malformed."""
    if not isinstance(data, dict):
        raise ValueError("Config must be a mapping at the top level")

    if "commands" not in data:
        raise ValueError("Config must include a 'commands' key")

    commands = data["commands"]
    if not isinstance(commands, list) or len(commands) == 0:
        raise ValueError("'commands' must be a non-empty list")

    for i, cmd in enumerate(commands):
        if not isinstance(cmd, str) or not cmd.strip():
            raise ValueError(f"Command at index {i} must be a non-empty string")

    timeout = data.get("timeout")
    if timeout is not None and (not isinstance(timeout, (int, float)) or timeout <= 0):
        raise ValueError("'timeout' must be a positive number")

    repeat = data.get("repeat")
    if repeat is not None and (not isinstance(repeat, int) or repeat < 1):
        raise ValueError("'repeat' must be a positive integer")

    notify = data.get("notify")
    if notify is not None:
        if not isinstance(notify, dict):
            raise ValueError("'notify' must be a mapping")
        min_f = notify.get("min_failures")
        if min_f is not None and (not isinstance(min_f, int) or min_f < 0):
            raise ValueError("'notify.min_failures' must be a non-negative integer")
