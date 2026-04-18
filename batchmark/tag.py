from dataclasses import dataclass, field
from typing import List, Dict
from batchmark.runner import CommandResult


@dataclass
class TaggedResult:
    result: CommandResult
    tags: List[str] = field(default_factory=list)


def tag_results(
    results: List[CommandResult],
    tag_map: Dict[str, List[str]],
) -> List[TaggedResult]:
    """Attach tags to results based on a mapping of command -> tags."""
    tagged = []
    for r in results:
        tags = tag_map.get(r.command, [])
        tagged.append(TaggedResult(result=r, tags=tags))
    return tagged


def filter_by_tag(tagged: List[TaggedResult], tag: str) -> List[TaggedResult]:
    """Return only TaggedResults that include the given tag."""
    return [t for t in tagged if tag in t.tags]


def group_by_tag(tagged: List[TaggedResult]) -> Dict[str, List[CommandResult]]:
    """Group results by tag. A result may appear under multiple tags."""
    groups: Dict[str, List[CommandResult]] = {}
    for t in tagged:
        for tag in t.tags:
            groups.setdefault(tag, []).append(t.result)
    return groups


def list_tags(tagged: List[TaggedResult]) -> List[str]:
    """Return a sorted list of unique tags across all results."""
    seen = set()
    for t in tagged:
        seen.update(t.tags)
    return sorted(seen)
