"""Output truncation utilities for batchmark reports."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class TruncateConfig:
    max_stdout: Optional[int] = None  # max chars for stdout
    max_stderr: Optional[int] = None  # max chars for stderr
    ellipsis: str = "..."


def truncate_string(s: str, max_len: Optional[int], ellipsis: str = "...") -> str:
    """Truncate a string to max_len characters, appending ellipsis if cut."""
    if max_len is None or len(s) <= max_len:
        return s
    if max_len <= len(ellipsis):
        return ellipsis[:max_len]
    return s[: max_len - len(ellipsis)] + ellipsis


def truncate_result_dict(result: dict, cfg: TruncateConfig) -> dict:
    """Return a copy of result dict with stdout/stderr truncated per config."""
    out = dict(result)
    if "stdout" in out and isinstance(out["stdout"], str):
        out["stdout"] = truncate_string(out["stdout"], cfg.max_stdout, cfg.ellipsis)
    if "stderr" in out and isinstance(out["stderr"], str):
        out["stderr"] = truncate_string(out["stderr"], cfg.max_stderr, cfg.ellipsis)
    return out


def truncate_results(results: list, cfg: TruncateConfig) -> list:
    """Apply truncation to a list of result dicts."""
    return [truncate_result_dict(r, cfg) for r in results]


def parse_truncate_config(raw: dict) -> TruncateConfig:
    """Build TruncateConfig from a raw config dict (e.g. loaded from YAML)."""
    section = raw.get("truncate", {})
    return TruncateConfig(
        max_stdout=section.get("max_stdout"),
        max_stderr=section.get("max_stderr"),
        ellipsis=section.get("ellipsis", "..."),
    )
