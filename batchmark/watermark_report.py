"""Formatting helpers for watermark results."""
from __future__ import annotations

import json
from typing import List

from batchmark.watermark import WatermarkEntry, watermarks_to_dicts

_RESET = "\033[0m"
_RED = "\033[31m"
_GREEN = "\033[32m"


def _flag(entry: WatermarkEntry) -> str:
    if entry.high_broken:
        return f"{_RED}NEW HIGH{_RESET}"
    if entry.low_broken:
        return f"{_GREEN}NEW LOW{_RESET}"
    return ""


def format_watermark_json(entries: List[WatermarkEntry]) -> str:
    return json.dumps(watermarks_to_dicts(entries), indent=2)


def format_watermark_table(entries: List[WatermarkEntry]) -> str:
    if not entries:
        return "No watermark data."

    header = f"{'Command':<40} {'Current':>10} {'High':>10} {'Low':>10}  Flag"
    sep = "-" * len(header)
    lines = [header, sep]

    for e in entries:
        high_s = f"{e.high:.4f}" if e.high is not None else "N/A"
        low_s = f"{e.low:.4f}" if e.low is not None else "N/A"
        flag = _flag(e)
        lines.append(
            f"{e.command:<40} {e.current:>10.4f} {high_s:>10} {low_s:>10}  {flag}"
        )

    return "\n".join(lines)


def watermark_summary(entries: List[WatermarkEntry]) -> str:
    highs = sum(1 for e in entries if e.high_broken)
    lows = sum(1 for e in entries if e.low_broken)
    return (
        f"Watermark summary: {len(entries)} command(s) | "
        f"{highs} new high(s) | {lows} new low(s)"
    )
