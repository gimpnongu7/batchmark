"""CPU and memory profiling support for benchmarked commands."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
import resource
import time

from batchmark.runner import CommandResult


@dataclass
class ProfileSnapshot:
    command: str
    wall_time: float
    user_time: float
    sys_time: float
    max_rss_kb: int  # peak resident set size in KB

    @property
    def cpu_time(self) -> float:
        return self.user_time + self.sys_time

    @property
    def cpu_efficiency(self) -> Optional[float]:
        """cpu_time / wall_time — >1 means parallel, <1 means I/O bound."""
        if self.wall_time == 0:
            return None
        return round(self.cpu_time / self.wall_time, 4)


def snapshot_from_rusage(command: str, wall_time: float, usage) -> ProfileSnapshot:
    return ProfileSnapshot(
        command=command,
        wall_time=round(wall_time, 6),
        user_time=round(usage.ru_utime, 6),
        sys_time=round(usage.ru_stime, 6),
        max_rss_kb=usage.ru_maxrss,
    )


def profile_result(result: CommandResult) -> ProfileSnapshot:
    """Build a ProfileSnapshot from a CommandResult (best-effort from timing)."""
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    return ProfileSnapshot(
        command=result.command,
        wall_time=result.duration,
        user_time=round(usage.ru_utime, 6),
        sys_time=round(usage.ru_stime, 6),
        max_rss_kb=usage.ru_maxrss,
    )


def profile_to_dict(snap: ProfileSnapshot) -> dict:
    return {
        "command": snap.command,
        "wall_time": snap.wall_time,
        "user_time": snap.user_time,
        "sys_time": snap.sys_time,
        "cpu_time": snap.cpu_time,
        "cpu_efficiency": snap.cpu_efficiency,
        "max_rss_kb": snap.max_rss_kb,
    }


def format_profile_table(snapshots: List[ProfileSnapshot]) -> str:
    header = f"{'Command':<30} {'Wall(s)':>8} {'CPU(s)':>8} {'Eff':>6} {'RSS(KB)':>9}"
    sep = "-" * len(header)
    rows = [header, sep]
    for s in snapshots:
        eff = f"{s.cpu_efficiency:.3f}" if s.cpu_efficiency is not None else "N/A"
        rows.append(
            f"{s.command[:30]:<30} {s.wall_time:>8.3f} {s.cpu_time:>8.3f} {eff:>6} {s.max_rss_kb:>9}"
        )
    return "\n".join(rows)
