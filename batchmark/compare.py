"""Compare results across two benchmark runs."""
from dataclasses import dataclass
from typing import Dict, List, Optional
from batchmark.runner import CommandResult


@dataclass
class CompareEntry:
    command: str
    duration_a: Optional[float]
    duration_b: Optional[float]
    delta: Optional[float]
    pct_change: Optional[float]
    status_a: Optional[str]
    status_b: Optional[str]


def _index_results(results: List[CommandResult]) -> Dict[str, CommandResult]:
    return {r.command: r for r in results}


def compare_runs(
    results_a: List[CommandResult],
    results_b: List[CommandResult],
) -> List[CompareEntry]:
    """Compare two lists of CommandResult by command name."""
    index_a = _index_results(results_a)
    index_b = _index_results(results_b)
    all_commands = sorted(set(index_a) | set(index_b))

    entries = []
    for cmd in all_commands:
        a = index_a.get(cmd)
        b = index_b.get(cmd)
        dur_a = a.duration if a else None
        dur_b = b.duration if b else None

        if dur_a is not None and dur_b is not None:
            delta = dur_b - dur_a
            pct = (delta / dur_a * 100) if dur_a != 0 else None
        else:
            delta = None
            pct = None

        entries.append(CompareEntry(
            command=cmd,
            duration_a=dur_a,
            duration_b=dur_b,
            delta=delta,
            pct_change=pct,
            status_a=a.status if a else None,
            status_b=b.status if b else None,
        ))
    return entries


def format_compare_table(entries: List[CompareEntry]) -> str:
    lines = [
        f"{'Command':<40} {'Run A':>10} {'Run B':>10} {'Delta':>10} {'Change':>10}",
        "-" * 82,
    ]
    for e in entries:
        dur_a = f"{e.duration_a:.3f}s" if e.duration_a is not None else "N/A"
        dur_b = f"{e.duration_b:.3f}s" if e.duration_b is not None else "N/A"
        delta = f"{e.delta:+.3f}s" if e.delta is not None else "N/A"
        pct = f"{e.pct_change:+.1f}%" if e.pct_change is not None else "N/A"
        lines.append(f"{e.command:<40} {dur_a:>10} {dur_b:>10} {delta:>10} {pct:>10}")
    return "\n".join(lines)
