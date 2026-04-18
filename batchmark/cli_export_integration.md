# Export Feature Integration

## Overview

The export feature lets users save benchmark results to **CSV** or **Markdown** files via CLI flags.

## New Flags

Add these arguments to `build_parser()` in `cli.py`:

```python
parser.add_argument(
    "--export",
    metavar="FILE",
    help="Export results to FILE (.csv or .md/.markdown)",
)
parser.add_argument(
    "--export-format",
    choices=["csv", "markdown"],
    default=None,
    help="Force export format (default: inferred from file extension)",
)
```

## Integration in `main()`

After running the batch and before printing output, add:

```python
from batchmark.cli_export import handle_export

handle_export(results, args.export, args.export_format)
```

## Example Usage

```bash
# Export to CSV
batchmark config.yaml --export results.csv

# Export to Markdown
batchmark config.yaml --export report.md

# Force format explicitly
batchmark config.yaml --export output.txt --export-format csv
```

## File Format Notes

- **CSV**: one row per command with columns: command, status, duration, returncode, stdout, stderr
- **Markdown**: table of results followed by a stats summary block
