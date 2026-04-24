"""Reporting helpers for spike detection results."""
from __future__ import annotations

import json
from typing import List

from batchmark.spike import SpikeEntry


def entry_to_dict(entry: SpikeEntry) -> dict:
    return {
        "command": entry.command,
        "duration": entry.duration,
        "status": entry.result.status,
        "rolling_mean": round(entry.rolling_mean, 4) if entry.rolling_mean is not None else None,
        "ratio": round(entry.ratio, 4) if entry.ratio is not None else None,
        "is_spike": entry.is_spike,
    }


def format_spike_json(entries: List[SpikeEntry]) -> str:
    return json.dumps([entry_to_dict(e) for e in entries], indent=2)


def format_spike_table(entries: List[SpikeEntry]) -> str:
    header = f"{'Command':<40} {'Duration':>10} {'RollingMean':>12} {'Ratio':>8} {'Spike':>6}"
    sep = "-" * len(header)
    lines = [header, sep]
    for e in entries:
        rm = f"{e.rolling_mean:.4f}" if e.rolling_mean is not None else "N/A"
        ratio = f"{e.ratio:.2f}x" if e.ratio is not None else "N/A"
        spike_flag = "YES" if e.is_spike else ""
        cmd = e.command[:38] if len(e.command) > 38 else e.command
        lines.append(f"{cmd:<40} {e.duration:>10.4f} {rm:>12} {ratio:>8} {spike_flag:>6}")
    return "\n".join(lines)


def spike_summary(entries: List[SpikeEntry]) -> str:
    total = len(entries)
    spikes = sum(1 for e in entries if e.is_spike)
    return f"Spike detection: {spikes}/{total} commands flagged as spikes."
