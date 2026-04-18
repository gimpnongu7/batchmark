"""CLI helpers for --export flag integration."""
from __future__ import annotations
import os
from typing import List, Optional
from batchmark.runner import CommandResult
from batchmark.export import write_export


SUPPORTED_FORMATS = ("csv", "markdown")


def infer_format(path: str) -> str:
    """Infer export format from file extension."""
    ext = os.path.splitext(path)[1].lower()
    mapping = {".csv": "csv", ".md": "markdown", ".markdown": "markdown"}
    if ext not in mapping:
        raise ValueError(
            f"Cannot infer export format from extension '{ext}'. "
            f"Use one of: .csv, .md, .markdown"
        )
    return mapping[ext]


def handle_export(
    results: List[CommandResult],
    export_path: Optional[str],
    export_fmt: Optional[str],
) -> None:
    """Write export file if export_path is provided."""
    if not export_path:
        return
    fmt = export_fmt or infer_format(export_path)
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported export format: {fmt}. Choose from {SUPPORTED_FORMATS}")
    write_export(results, export_path, fmt)
    print(f"[batchmark] Exported results to {export_path} ({fmt})")
