"""Redact sensitive values from commands and environment variables."""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class RedactConfig:
    patterns: List[str] = field(default_factory=list)
    placeholder: str = "***"
    redact_env_keys: List[str] = field(default_factory=list)


def _compile(patterns: List[str]) -> List[re.Pattern]:
    return [re.compile(p) for p in patterns]


def redact_string(text: str, config: RedactConfig) -> str:
    """Replace matches of any pattern in text with placeholder."""
    result = text
    for pat in _compile(config.patterns):
        result = pat.sub(config.placeholder, result)
    return result


def redact_env(env: dict, config: RedactConfig) -> dict:
    """Return a copy of env with sensitive keys replaced."""
    redacted = {}
    keys_upper = [k.upper() for k in config.redact_env_keys]
    for k, v in env.items():
        if k.upper() in keys_upper:
            redacted[k] = config.placeholder
        else:
            redacted[k] = v
    return redacted


def redact_result_dict(d: dict, config: RedactConfig) -> dict:
    """Redact command string inside a result dict."""
    out = dict(d)
    if "command" in out:
        out["command"] = redact_string(out["command"], config)
    if "stdout" in out and out["stdout"]:
        out["stdout"] = redact_string(out["stdout"], config)
    if "stderr" in out and out["stderr"]:
        out["stderr"] = redact_string(out["stderr"], config)
    return out


def load_redact_config(raw: dict) -> RedactConfig:
    """Build RedactConfig from a config dict (e.g. loaded from YAML/JSON)."""
    section = raw.get("redact", {})
    return RedactConfig(
        patterns=section.get("patterns", []),
        placeholder=section.get("placeholder", "***"),
        redact_env_keys=section.get("env_keys", []),
    )
