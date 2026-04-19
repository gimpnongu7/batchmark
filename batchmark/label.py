"""Label results with arbitrary key-value metadata."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from batchmark.runner import CommandResult


@dataclass
class LabeledResult:
    result: CommandResult
    labels: Dict[str, str] = field(default_factory=dict)


def label_results(
    results: List[CommandResult],
    label_map: Dict[str, Dict[str, str]],
) -> List[LabeledResult]:
    """Attach labels to results by matching command string."""
    labeled = []
    for r in results:
        labels = label_map.get(r.command, {})
        labeled.append(LabeledResult(result=r, labels=labels))
    return labeled


def filter_by_label(labeled: List[LabeledResult], key: str, value: str) -> List[LabeledResult]:
    """Return only results where labels[key] == value."""
    return [lr for lr in labeled if lr.labels.get(key) == value]


def group_by_label(labeled: List[LabeledResult], key: str) -> Dict[str, List[LabeledResult]]:
    """Group labeled results by the value of a given label key."""
    groups: Dict[str, List[LabeledResult]] = {}
    for lr in labeled:
        val = lr.labels.get(key, "")
        groups.setdefault(val, []).append(lr)
    return groups


def list_label_keys(labeled: List[LabeledResult]) -> List[str]:
    """Return sorted unique label keys across all results."""
    keys = set()
    for lr in labeled:
        keys.update(lr.labels.keys())
    return sorted(keys)


def labeled_to_dict(lr: LabeledResult) -> dict:
    return {
        "command": lr.result.command,
        "status": lr.result.status,
        "duration": lr.result.duration,
        "labels": lr.labels,
    }
