from __future__ import annotations
import json
from typing import List
from batchmark.heatmap import HeatmapCell, build_heatmap, format_heatmap_table, HeatmapConfig
from batchmark.runner import CommandResult


def cell_to_dict(cell: HeatmapCell) -> dict:
    return {
        "command": cell.command,
        "duration": cell.duration,
        "status": cell.status,
        "intensity": cell.intensity,
        "symbol": cell.symbol,
    }


def format_heatmap_json(cells: List[HeatmapCell]) -> str:
    return json.dumps([cell_to_dict(c) for c in cells], indent=2)


def heatmap_summary(cells: List[HeatmapCell]) -> dict:
    if not cells:
        return {"total": 0, "hottest": None, "coolest": None}
    hottest = max(cells, key=lambda c: c.intensity)
    coolest = min(cells, key=lambda c: c.intensity)
    return {
        "total": len(cells),
        "hottest": cell_to_dict(hottest),
        "coolest": cell_to_dict(coolest),
    }


def report_heatmap(
    results: List[CommandResult],
    cfg: HeatmapConfig,
    fmt: str = "table",
) -> str:
    cells = build_heatmap(results, cfg)
    if fmt == "json":
        return format_heatmap_json(cells)
    return format_heatmap_table(cells)
