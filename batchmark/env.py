"""Environment variable injection for batchmark commands."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import os


@dataclass
class EnvConfig:
    base: Dict[str, str] = field(default_factory=dict)
    inherit: bool = True


def build_env(config: EnvConfig, overrides: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Build the environment dict for a command."""
    env: Dict[str, str] = {}
    if config.inherit:
        env.update(os.environ)
    env.update(config.base)
    if overrides:
        env.update(overrides)
    return env


def parse_env_list(pairs: List[str]) -> Dict[str, str]:
    """Parse a list of KEY=VALUE strings into a dict."""
    result: Dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"Invalid env pair (expected KEY=VALUE): {pair!r}")
        key, _, value = pair.partition("=")
        result[key.strip()] = value
    return result


def load_env_config(raw: dict) -> EnvConfig:
    """Load EnvConfig from a config dict (e.g. parsed YAML/JSON)."""
    env_section = raw.get("env", {})
    base = env_section.get("vars", {})
    inherit = env_section.get("inherit", True)
    if not isinstance(base, dict):
        raise ValueError("env.vars must be a mapping of KEY: VALUE")
    return EnvConfig(base=base, inherit=inherit)
