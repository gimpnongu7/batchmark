"""Export batch results to CSV and Markdown formats."""
from __future__ import annotations
import csv
import io
from typing import List
from batchmark.runner import CommandResult
from batchmark.stats import compute_stats


def format_csv(results: List[CommandResult]) -> str:
    """Return CSV string of all command results."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["command", "status", "duration", "returncode", "stdout", "stderr"])
    for r in results:
        writer.writerow([
            r.command,
            r.status,
            f"{r.duration:.4f}",
            r.returncode,
            r.stdout.strip().replace("\n", " "),
            r.stderr.strip().replace("\n", " "),
        ])
    return output.getvalue()


def format_markdown(results: List[CommandResult]) -> str:
    """Return Markdown table string of all command results."""
    lines = []
    lines.append("| Command | Status | Duration (s) | Return Code |")
    lines.append("|---------|--------|-------------|-------------|")
    for r in results:
        lines.append(
            f"| `{r.command}` | {r.status} | {r.duration:.4f} | {r.returncode} |"
        )
    lines.append("")
    stats = compute_stats(results)
    lines.append(f"**Total:** {stats.total}  ")
    lines.append(f"**Passed:** {stats.passed}  ")
    lines.append(f"**Failed:** {stats.failed}  ")
    lines.append(f"**Avg Duration:** {stats.avg_duration:.4f}s  ")
    lines.append(f"**Median Duration:** {stats.median_duration:.4f}s  ")
    return "\n".join(lines) + "\n"


def write_export(results: List[CommandResult], path: str, fmt: str) -> None:
    """Write exported results to a file. fmt must be 'csv' or 'markdown'."""
    if fmt == "csv":
        content = format_csv(results)
    elif fmt == "markdown":
        content = format_markdown(results)
    else:
        raise ValueError(f"Unsupported export format: {fmt}")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
