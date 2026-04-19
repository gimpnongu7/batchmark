from __future__ import annotations
import json
from typing import List
from batchmark.score import ScoredResult


def scored_to_dict(sr: ScoredResult) -> dict:
    return {
        "command": sr.command,
        "status": sr.status,
        "duration": sr.duration,
        "score": sr.score,
        "grade": sr.grade,
    }


def format_score_json(scored: List[ScoredResult]) -> str:
    return json.dumps([scored_to_dict(s) for s in scored], indent=2)


def format_score_table(scored: List[ScoredResult]) -> str:
    if not scored:
        return "No results."
    header = f"{'Command':<40} {'Status':<10} {'Duration':>10} {'Score':>8} {'Grade':>6}"
    sep = "-" * len(header)
    rows = [header, sep]
    for s in scored:
        rows.append(
            f"{s.command:<40} {s.status:<10} {s.duration:>10.3f} {s.score:>8.2f} {s.grade:>6}"
        )
    total = len(scored)
    mean_score = sum(s.score for s in scored) / total if total else 0.0
    rows.append(sep)
    rows.append(f"Total: {total}  Mean score: {mean_score:.2f}")
    return "\n".join(rows)
