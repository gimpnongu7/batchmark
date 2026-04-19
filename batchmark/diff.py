"""Diff two result sets by command, highlighting changes in status and duration."""
from dataclasses import dataclass
from typing import List, Optional, Dict
from batchmark.runner import CommandResult


@dataclass
class DiffEntry:
    command: str
    status_a: Optional[str]
    status_b: Optional[str]
    duration_a: Optional[float]
    duration_b: Optional[float]

    @property
    def status_changed(self) -> bool:
        return self.status_a != self.status_b

    @property
    def duration_delta(self) -> Optional[float]:
        if self.duration_a is not None and self.duration_b is not None:
            return self.duration_b - self.duration_a
        return None

    @property
    def duration_pct(self) -> Optional[float]:
        if self.duration_a and self.duration_a > 0 and self.duration_b is not None:
            return (self.duration_b - self.duration_a) / self.duration_a * 100
        return None


def _index(results: List[CommandResult]) -> Dict[str, CommandResult]:
    return {r.command: r for r in results}


def diff_runs(a: List[CommandResult], b: List[CommandResult]) -> List[DiffEntry]:
    idx_a = _index(a)
    idx_b = _index(b)
    commands = sorted(set(idx_a) | set(idx_b))
    entries = []
    for cmd in commands:
        ra = idx_a.get(cmd)
        rb = idx_b.get(cmd)
        entries.append(DiffEntry(
            command=cmd,
            status_a=ra.status if ra else None,
            status_b=rb.status if rb else None,
            duration_a=ra.duration if ra else None,
            duration_b=rb.duration if rb else None,
        ))
    return entries


def format_diff_table(entries: List[DiffEntry]) -> str:
    header = f"{'Command':<40} {'Status A':<12} {'Status B':<12} {'Dur A':>8} {'Dur B':>8} {'Delta':>8} {'Pct':>7}"
    sep = "-" * len(header)
    rows = [header, sep]
    for e in entries:
        da = f"{e.duration_a:.3f}" if e.duration_a is not None else "n/a"
        db = f"{e.duration_b:.3f}" if e.duration_b is not None else "n/a"
        delta = f"{e.duration_delta:+.3f}" if e.duration_delta is not None else "n/a"
        pct = f"{e.duration_pct:+.1f}%" if e.duration_pct is not None else "n/a"
        flag = " *" if e.status_changed else ""
        rows.append(f"{e.command:<40} {(e.status_a or 'missing'):<12} {(e.status_b or 'missing'):<12} {da:>8} {db:>8} {delta:>8} {pct:>7}{flag}")
    return "\n".join(rows)
