"""Snapshot module: capture and compare point-in-time result sets.

Allows saving a named snapshot of a batch run and later diffing against
a new run to see what changed in terms of status or duration.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

from batchmark.runner import CommandResult


@dataclass
class SnapshotEntry:
    """A single command's data stored in a snapshot."""
    command: str
    status: str
    duration: float
    stdout: str = ""
    stderr: str = ""


@dataclass
class SnapshotDiff:
    """Difference between a snapshot entry and a current result."""
    command: str
    old_status: Optional[str]    # None if command is new
    new_status: Optional[str]    # None if command was removed
    old_duration: Optional[float]
    new_duration: Optional[float]

    @property
    def status_changed(self) -> bool:
        return self.old_status != self.new_status

    @property
    def duration_delta(self) -> Optional[float]:
        if self.old_duration is None or self.new_duration is None:
            return None
        return self.new_duration - self.old_duration

    @property
    def is_new(self) -> bool:
        return self.old_status is None

    @property
    def is_removed(self) -> bool:
        return self.new_status is None


def _result_to_entry(result: CommandResult) -> SnapshotEntry:
    return SnapshotEntry(
        command=result.command,
        status=result.status,
        duration=result.duration,
        stdout=result.stdout or "",
        stderr=result.stderr or "",
    )


def save_snapshot(results: List[CommandResult], path: str, label: str = "") -> None:
    """Persist a batch of results to a JSON snapshot file."""
    entries = [vars(_result_to_entry(r)) for r in results]
    payload = {"label": label, "entries": entries}
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)


def load_snapshot(path: str) -> List[SnapshotEntry]:
    """Load a previously saved snapshot from disk."""
    with open(path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    return [
        SnapshotEntry(
            command=e["command"],
            status=e["status"],
            duration=e["duration"],
            stdout=e.get("stdout", ""),
            stderr=e.get("stderr", ""),
        )
        for e in payload.get("entries", [])
    ]


def diff_snapshot(
    snapshot: List[SnapshotEntry],
    current: List[CommandResult],
) -> List[SnapshotDiff]:
    """Compare a snapshot against a current run and return per-command diffs.

    Commands present in only one side are included with None values for the
    missing side.
    """
    old_index: Dict[str, SnapshotEntry] = {e.command: e for e in snapshot}
    new_index: Dict[str, CommandResult] = {r.command: r for r in current}

    all_commands = sorted(set(old_index) | set(new_index))
    diffs: List[SnapshotDiff] = []

    for cmd in all_commands:
        old = old_index.get(cmd)
        new = new_index.get(cmd)
        diffs.append(
            SnapshotDiff(
                command=cmd,
                old_status=old.status if old else None,
                new_status=new.status if new else None,
                old_duration=old.duration if old else None,
                new_duration=new.duration if new else None,
            )
        )

    return diffs
