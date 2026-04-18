# CLI Compare Integration

The `compare` feature allows users to diff two benchmark runs side by side.

## Usage

```bash
batchmark compare run_a.json run_b.json
batchmark compare run_a.json run_b.json --output diff.md
batchmark compare run_a.json run_b.json --format json
```

## How It Works

1. Load two previously saved JSON result files (produced via `--output run.json`).
2. Match commands by name across both runs.
3. Compute delta and percent change in duration.
4. Commands missing from one run are shown with `N/A`.

## Output Example

```
Command                                   Run A      Run B      Delta     Change
----------------------------------------------------------------------------------
echo hello                               0.100s     0.080s    -0.020s    -20.0%
sleep 1                                  1.000s     1.200s    +0.200s    +20.0%
ls /tmp                                  0.050s        N/A        N/A       N/A
```

## Error Handling

- If either file does not exist, the CLI exits with a clear message and a non-zero exit code.
- If a file is not valid JSON or is missing the expected `results` key, an error is shown indicating which file is malformed.
- If both files contain no overlapping commands, a warning is printed but the table is still rendered.

## Integration Points

- `batchmark/compare.py`: core logic — `compare_runs`, `format_compare_table`
- `batchmark/cli.py`: add `compare` subcommand to `build_parser`
- Input files must be JSON exports from a prior `batchmark` run

## Planned CLI Args

| Argument | Description |
|---|---|
| `file_a` | Path to first run JSON |
| `file_b` | Path to second run JSON |
| `--output` | Optional file to write comparison table |
| `--format` | `table` (default) or `json` |
