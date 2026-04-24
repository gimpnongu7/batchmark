"""Pipeline: chain multiple batch runs where output of one feeds the next."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Callable
from batchmark.runner import CommandResult, run_batch


@dataclass
class PipelineStage:
    name: str
    commands: List[str]
    timeout: Optional[float] = None
    stop_on_failure: bool = False


@dataclass
class PipelineResult:
    stage: str
    results: List[CommandResult]
    skipped: bool = False

    @property
    def success(self) -> bool:
        return not self.skipped and all(r.exit_code == 0 for r in self.results)

    @property
    def total_duration(self) -> float:
        return sum(r.duration for r in self.results)

    @property
    def failed_commands(self) -> List[CommandResult]:
        """Return only the results that had a non-zero exit code."""
        return [r for r in self.results if r.exit_code != 0]


def run_pipeline(
    stages: List[PipelineStage],
    on_stage: Optional[Callable[[PipelineResult], None]] = None,
) -> List[PipelineResult]:
    """Run stages sequentially; skip remaining stages if stop_on_failure triggers."""
    pipeline_results: List[PipelineResult] = []
    abort = False

    for stage in stages:
        if abort:
            pipeline_results.append(PipelineResult(stage=stage.name, results=[], skipped=True))
            continue

        results = run_batch(stage.commands, timeout=stage.timeout)
        pr = PipelineResult(stage=stage.name, results=results)

        if on_stage:
            on_stage(pr)

        pipeline_results.append(pr)

        if stage.stop_on_failure and not pr.success:
            abort = True

    return pipeline_results


def pipeline_summary(results: List[PipelineResult]) -> dict:
    """Return a high-level summary dict for a completed pipeline run."""
    total_stages = len(results)
    passed = sum(1 for r in results if r.success)
    skipped = sum(1 for r in results if r.skipped)
    failed = total_stages - passed - skipped
    return {
        "total_stages": total_stages,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "total_duration": sum(r.total_duration for r in results),
    }


def parse_pipeline_config(raw: dict) -> List[PipelineStage]:
    stages = []
    for entry in raw.get("stages", []):
        stages.append(PipelineStage(
            name=entry["name"],
            commands=entry["commands"],
            timeout=entry.get("timeout"),
            stop_on_failure=entry.get("stop_on_failure", False),
        ))
    return stages
