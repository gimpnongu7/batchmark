"""Split a batch of results into named groups based on rules."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional
from batchmark.runner import CommandResult


@dataclass
class SplitRule:
    name: str
    predicate: Callable[[CommandResult], bool]


@dataclass
class SplitConfig:
    rules: List[SplitRule] = field(default_factory=list)
    default_group: str = "other"


@dataclass
class SplitResult:
    groups: Dict[str, List[CommandResult]] = field(default_factory=dict)

    def get(self, name: str) -> List[CommandResult]:
        return self.groups.get(name, [])

    def group_names(self) -> List[str]:
        return list(self.groups.keys())

    def summary(self) -> Dict[str, int]:
        """Return a dict mapping each group name to the count of results in it."""
        return {name: len(results) for name, results in self.groups.items()}


def split_results(results: List[CommandResult], config: SplitConfig) -> SplitResult:
    """Assign each result to the first matching rule group, or default."""
    groups: Dict[str, List[CommandResult]] = {}
    for result in results:
        assigned = False
        for rule in config.rules:
            if rule.predicate(result):
                groups.setdefault(rule.name, []).append(result)
                assigned = True
                break
        if not assigned:
            groups.setdefault(config.default_group, []).append(result)
    return SplitResult(groups=groups)


def parse_split_config(raw: dict) -> SplitConfig:
    """Build a SplitConfig from a plain dict (e.g. loaded from YAML).

    Supported rule keys:
      - status: "success" | "failure" | "timeout"
      - min_duration / max_duration (seconds, float)
      - contains: substring in command string
    """
    rules = []
    for entry in raw.get("rules", []):
        name = entry.get("name")
        if not name:
            raise ValueError(f"Each split rule must have a 'name' field: {entry!r}")
        predicates: List[Callable[[CommandResult], bool]] = []
        if "status" in entry:
            s = entry["status"]
            predicates.append(lambda r, s=s: r.status == s)
        if "min_duration" in entry:
            mn = float(entry["min_duration"])
            predicates.append(lambda r, mn=mn: r.duration >= mn)
        if "max_duration" in entry:
            mx = float(entry["max_duration"])
            predicates.append(lambda r, mx=mx: r.duration <= mx)
        if "contains" in entry:
            sub = entry["contains"]
            predicates.append(lambda r, sub=sub: sub in r.command)

        def make_pred(preds):
            return lambda r: all(p(r) for p in preds)

        rules.append(SplitRule(name=name, predicate=make_pred(predicates)))
    return SplitConfig(rules=rules, default_group=raw.get("default_group", "other"))
