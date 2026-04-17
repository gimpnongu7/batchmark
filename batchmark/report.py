import json
from typing import Any
from batchmark.runner import CommandResult


def results_to_dict(results: list[CommandResult]) -> dict[str, Any]:
    total = len(results)
    passed = sum(1 for r in results if r.success)
    durations = [r.duration_seconds for r in results]

    return {
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "total_duration_seconds": round(sum(durations), 6),
            "avg_duration_seconds": round(sum(durations) / total, 6) if total else 0,
            "min_duration_seconds": round(min(durations), 6) if durations else 0,
            "max_duration_seconds": round(max(durations), 6) if durations else 0,
        },
        "commands": [
            {
                "command": r.command,
                "exit_code": r.exit_code,
                "success": r.success,
                "duration_seconds": r.duration_seconds,
                "stdout": r.stdout.strip(),
                "stderr": r.stderr.strip(),
            }
            for r in results
        ],
    }


def format_json(results: list[CommandResult]) -> str:
    return json.dumps(results_to_dict(results), indent=2)


def format_table(results: list[CommandResult]) -> str:
    lines = [
        f"{'COMMAND':<50} {'STATUS':<8} {'DURATION':>12}",
        "-" * 72,
    ]
    for r in results:
        status = "OK" if r.success else "FAIL"
        cmd_display = r.command if len(r.command) <= 48 else r.command[:45] + "..."
        lines.append(f"{cmd_display:<50} {status:<8} {r.duration_seconds:>10.4f}s")

    data = results_to_dict(results)["summary"]
    lines += [
        "-" * 72,
        f"Total: {data['total']}  Passed: {data['passed']}  Failed: {data['failed']}",
        f"Duration — total: {data['total_duration_seconds']}s  "
        f"avg: {data['avg_duration_seconds']}s  "
        f"min: {data['min_duration_seconds']}s  "
        f"max: {data['max_duration_seconds']}s",
    ]
    return "\n".join(lines)
