"""Group results by a key field and compute per-group stats."""
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional
from batchmark.runner import CommandResult
from batchmark.stats import compute_stats, BatchStats


@dataclass
class GroupEntry:
    name: str
    results: List[CommandResult]
    stats: Optional[BatchStats] = None

    def __post_init__(self):
        if self.stats is None and self.results:
            self.stats = compute_stats(self.results)


def group_by(results: List[CommandResult], key: str) -> Dict[str, GroupEntry]:
    """Group results by a field: 'status', 'command', or a callable."""
    buckets: Dict[str, List[CommandResult]] = {}
    for r in results:
        if key == "status":
            k = r.status
        elif key == "command":
            k = r.command
        else:
            k = str(getattr(r, key, "unknown"))
        buckets.setdefault(k, []).append(r)
    return {name: GroupEntry(name=name, results=rs) for name, rs in buckets.items()}


def group_by_fn(results: List[CommandResult], fn: Callable[[CommandResult], str]) -> Dict[str, GroupEntry]:
    """Group results using an arbitrary callable."""
    buckets: Dict[str, List[CommandResult]] = {}
    for r in results:
        k = fn(r)
        buckets.setdefault(k, []).append(r)
    return {name: GroupEntry(name=name, results=rs) for name, rs in buckets.items()}


def format_group_table(groups: Dict[str, GroupEntry]) -> str:
    lines = [f"{'Group':<30} {'Count':>6} {'Mean':>10} {'Min':>10} {'Max':>10}"]
    lines.append("-" * 70)
    for name, entry in sorted(groups.items()):
        s = entry.stats
        if s:
            lines.append(f"{name:<30} {s.total:>6} {s.mean:>10.3f} {s.min:>10.3f} {s.max:>10.3f}")
        else:
            lines.append(f"{name:<30} {'0':>6} {'N/A':>10} {'N/A':>10} {'N/A':>10}")
    return "\n".join(lines)
