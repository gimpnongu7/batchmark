"""Correlate two sets of results by command and compute duration relationships."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

from batchmark.runner import CommandResult


@dataclass
class CorrelateEntry:
    command: str
    duration_a: Optional[float]
    duration_b: Optional[float]
    ratio: Optional[float]          # b / a
    delta: Optional[float]          # b - a
    in_both: bool


def _index(results: Sequence[CommandResult]) -> Dict[str, CommandResult]:
    return {r.command: r for r in results}


def correlate_runs(
    run_a: Sequence[CommandResult],
    run_b: Sequence[CommandResult],
) -> List[CorrelateEntry]:
    """Return one CorrelateEntry per unique command across both runs."""
    idx_a = _index(run_a)
    idx_b = _index(run_b)
    commands = sorted(set(idx_a) | set(idx_b))

    entries: List[CorrelateEntry] = []
    for cmd in commands:
        a = idx_a.get(cmd)
        b = idx_b.get(cmd)
        dur_a = a.duration if a else None
        dur_b = b.duration if b else None

        if dur_a is not None and dur_b is not None:
            ratio = (dur_b / dur_a) if dur_a != 0 else None
            delta = dur_b - dur_a
            in_both = True
        else:
            ratio = None
            delta = None
            in_both = False

        entries.append(
            CorrelateEntry(
                command=cmd,
                duration_a=dur_a,
                duration_b=dur_b,
                ratio=ratio,
                delta=delta,
                in_both=in_both,
            )
        )
    return entries


def format_correlate_table(entries: List[CorrelateEntry]) -> str:
    header = f"{'Command':<40} {'Dur A':>10} {'Dur B':>10} {'Delta':>10} {'Ratio':>8}"
    sep = "-" * len(header)
    rows = [header, sep]
    for e in entries:
        dur_a = f"{e.duration_a:.4f}" if e.duration_a is not None else "N/A"
        dur_b = f"{e.duration_b:.4f}" if e.duration_b is not None else "N/A"
        delta = f"{e.delta:+.4f}" if e.delta is not None else "N/A"
        ratio = f"{e.ratio:.3f}x" if e.ratio is not None else "N/A"
        rows.append(f"{e.command:<40} {dur_a:>10} {dur_b:>10} {delta:>10} {ratio:>8}")
    return "\n".join(rows)
