"""Reporting utilities for pipeline results."""
from __future__ import annotations
import json
from typing import List
from batchmark.pipeline import PipelineResult
from batchmark.report import results_to_dict


def pipeline_result_to_dict(pr: PipelineResult) -> dict:
    return {
        "stage": pr.stage,
        "skipped": pr.skipped,
        "success": pr.success,
        "total_duration": pr.total_duration,
        "commands": results_to_dict(pr.results) if not pr.skipped else [],
    }


def format_pipeline_json(pipeline_results: List[PipelineResult]) -> str:
    return json.dumps([pipeline_result_to_dict(pr) for pr in pipeline_results], indent=2)


def format_pipeline_table(pipeline_results: List[PipelineResult]) -> str:
    lines = [
        f"{'Stage':<20} {'Status':<10} {'Duration':>10} {'Commands':>10}",
        "-" * 54,
    ]
    for pr in pipeline_results:
        if pr.skipped:
            status = "SKIPPED"
            duration = "-"
            count = "-"
        else:
            status = "OK" if pr.success else "FAIL"
            duration = f"{pr.total_duration:.3f}s"
            count = str(len(pr.results))
        lines.append(f"{pr.stage:<20} {status:<10} {duration:>10} {count:>10}")
    return "\n".join(lines)
