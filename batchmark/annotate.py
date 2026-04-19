"""Attach free-form annotations (key/value metadata) to command results."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from batchmark.runner import CommandResult


@dataclass
class AnnotatedResult:
    result: CommandResult
    annotations: Dict[str, str] = field(default_factory=dict)

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self.annotations.get(key, default)


def annotate_results(
    results: List[CommandResult],
    annotation_map: Dict[str, Dict[str, str]],
) -> List[AnnotatedResult]:
    """Attach annotations to results by matching on command string."""
    annotated = []
    for r in results:
        ann = annotation_map.get(r.command, {})
        annotated.append(AnnotatedResult(result=r, annotations=dict(ann)))
    return annotated


def filter_by_annotation(
    annotated: List[AnnotatedResult],
    key: str,
    value: str,
) -> List[AnnotatedResult]:
    """Return only results where annotations[key] == value."""
    return [a for a in annotated if a.annotations.get(key) == value]


def group_by_annotation(
    annotated: List[AnnotatedResult],
    key: str,
) -> Dict[str, List[AnnotatedResult]]:
    """Group annotated results by the value of a given annotation key."""
    groups: Dict[str, List[AnnotatedResult]] = {}
    for a in annotated:
        val = a.annotations.get(key, "")
        groups.setdefault(val, []).append(a)
    return groups


def list_annotation_keys(annotated: List[AnnotatedResult]) -> List[str]:
    """Return sorted list of all annotation keys present across all results."""
    keys: set = set()
    for a in annotated:
        keys.update(a.annotations.keys())
    return sorted(keys)
