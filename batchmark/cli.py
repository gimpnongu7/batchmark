"""CLI entry point for batchmark."""
import argparse
import sys
import json
from pathlib import Path

from batchmark.runner import run_batch
from batchmark.report import format_json, format_table
from batchmark.config import load_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="batchmark",
        description="Benchmark batches of shell commands and output timing reports.",
    )
    parser.add_argument(
        "config",
        type=Path,
        help="Path to a YAML or JSON config file defining commands to benchmark.",
    )
    parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write output to a file instead of stdout.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Override timeout (seconds) for all commands.",
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error loading config: {exc}", file=sys.stderr)
        return 1

    timeout = args.timeout if args.timeout is not None else config.get("timeout")
    commands = config.get("commands", [])

    if not commands:
        print("No commands found in config.", file=sys.stderr)
        return 1

    results = run_batch(commands, timeout=timeout)

    output = format_json(results) if args.format == "json" else format_table(results)

    if args.output:
        args.output.write_text(output)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
