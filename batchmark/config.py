"""Config loader for batchmark — supports YAML and JSON."""
import json
from pathlib import Path
from typing import Any

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


def load_config(path: Path) -> dict[str, Any]:
    """Load a benchmark config from a YAML or JSON file.

    Expected structure::

        timeout: 30          # optional global timeout in seconds
        commands:
          - label: echo test
            cmd: echo hello
          - label: sleep short
            cmd: sleep 0.1
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    suffix = path.suffix.lower()
    text = path.read_text()

    if suffix in (".yaml", ".yml"):
        if not _YAML_AVAILABLE:
            raise ValueError("PyYAML is required to load YAML configs: pip install pyyaml")
        data = yaml.safe_load(text)
    elif suffix == ".json":
        data = json.loads(text)
    else:
        raise ValueError(f"Unsupported config format: '{suffix}'. Use .yaml, .yml, or .json.")

    if not isinstance(data, dict):
        raise ValueError("Config must be a mapping at the top level.")

    _validate_config(data)
    return data


def _validate_config(data: dict[str, Any]) -> None:
    commands = data.get("commands")
    if commands is None:
        raise ValueError("Config must contain a 'commands' list.")
    if not isinstance(commands, list):
        raise ValueError("'commands' must be a list.")
    for i, entry in enumerate(commands):
        if not isinstance(entry, dict):
            raise ValueError(f"commands[{i}] must be a mapping with 'cmd' key.")
        if "cmd" not in entry:
            raise ValueError(f"commands[{i}] is missing required key 'cmd'.")
