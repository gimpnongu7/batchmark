"""relay.py — forward results to an external HTTP endpoint."""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import List, Optional

from batchmark.runner import CommandResult


@dataclass
class RelayConfig:
    url: str
    method: str = "POST"
    headers: dict = field(default_factory=lambda: {"Content-Type": "application/json"})
    timeout: float = 5.0
    on_failure: str = "warn"  # "warn" | "raise" | "ignore"


@dataclass
class RelayResponse:
    status: int
    ok: bool
    body: str


def _result_to_dict(r: CommandResult) -> dict:
    return {
        "command": r.command,
        "returncode": r.returncode,
        "duration": r.duration,
        "stdout": r.stdout,
        "stderr": r.stderr,
        "timed_out": r.timed_out,
    }


def relay_result(result: CommandResult, cfg: RelayConfig) -> RelayResponse:
    payload = json.dumps(_result_to_dict(result)).encode()
    req = urllib.request.Request(
        cfg.url, data=payload, headers=cfg.headers, method=cfg.method
    )
    try:
        with urllib.request.urlopen(req, timeout=cfg.timeout) as resp:
            return RelayResponse(status=resp.status, ok=True, body=resp.read().decode())
    except urllib.error.HTTPError as exc:
        resp = RelayResponse(status=exc.code, ok=False, body=str(exc.reason))
    except Exception as exc:
        resp = RelayResponse(status=0, ok=False, body=str(exc))

    if cfg.on_failure == "raise":
        raise RuntimeError(f"relay failed: {resp.body}")
    if cfg.on_failure == "warn":
        import warnings
        warnings.warn(f"relay to {cfg.url} failed: {resp.body}")
    return resp


def relay_batch(results: List[CommandResult], cfg: RelayConfig) -> List[RelayResponse]:
    return [relay_result(r, cfg) for r in results]


def parse_relay_config(data: dict) -> Optional[RelayConfig]:
    raw = data.get("relay")
    if not raw:
        return None
    return RelayConfig(
        url=raw["url"],
        method=raw.get("method", "POST"),
        headers=raw.get("headers", {"Content-Type": "application/json"}),
        timeout=float(raw.get("timeout", 5.0)),
        on_failure=raw.get("on_failure", "warn"),
    )
