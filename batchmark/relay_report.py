"""relay_report.py — format relay responses for display."""
from __future__ import annotations

import json
from typing import List

from batchmark.relay import RelayResponse


def response_to_dict(resp: RelayResponse) -> dict:
    return {"status": resp.status, "ok": resp.ok, "body": resp.body}


def format_relay_json(responses: List[RelayResponse]) -> str:
    return json.dumps([response_to_dict(r) for r in responses], indent=2)


def format_relay_table(responses: List[RelayResponse]) -> str:
    lines = [f"{'STATUS':<8} {'OK':<6} BODY"]
    lines.append("-" * 50)
    for r in responses:
        ok_str = "yes" if r.ok else "no"
        body_preview = r.body[:30].replace("\n", " ")
        lines.append(f"{r.status:<8} {ok_str:<6} {body_preview}")
    return "\n".join(lines)


def relay_summary(responses: List[RelayResponse]) -> dict:
    total = len(responses)
    succeeded = sum(1 for r in responses if r.ok)
    failed = total - succeeded
    return {"total": total, "succeeded": succeeded, "failed": failed}
