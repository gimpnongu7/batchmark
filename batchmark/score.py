from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
from batchmark.runner import CommandResult


@dataclass
class ScoredResult:
    result: CommandResult
    score: float
    grade: str

    @property
    def command(self) -> str:
        return self.result.command

    @property
    def duration(self) -> float:
        return self.result.duration

    @property
    def status(self) -> str:
        return self.result.status


@dataclass
class ScoreConfig:
    max_duration: float = 10.0
    penalty_failure: float = 50.0
    penalty_timeout: float = 30.0
    weight_duration: float = 1.0


def _grade(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def score_result(result: CommandResult, cfg: ScoreConfig) -> ScoredResult:
    base = 100.0
    if result.status == "failure":
        base -= cfg.penalty_failure
    elif result.status == "timeout":
        base -= cfg.penalty_timeout
    duration_penalty = min(result.duration / max(cfg.max_duration, 1e-9), 1.0) * 100.0 * cfg.weight_duration
    raw = base - duration_penalty
    score = max(0.0, min(100.0, raw))
    return ScoredResult(result=result, score=round(score, 2), grade=_grade(score))


def score_results(results: List[CommandResult], cfg: Optional[ScoreConfig] = None) -> List[ScoredResult]:
    if cfg is None:
        cfg = ScoreConfig()
    return [score_result(r, cfg) for r in results]


def parse_score_config(raw: dict) -> ScoreConfig:
    return ScoreConfig(
        max_duration=float(raw.get("max_duration", 10.0)),
        penalty_failure=float(raw.get("penalty_failure", 50.0)),
        penalty_timeout=float(raw.get("penalty_timeout", 30.0)),
        weight_duration=float(raw.get("weight_duration", 1.0)),
    )
