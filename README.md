# batchmark

A CLI tool to benchmark batches of shell commands and output structured timing reports.

## Installation

```bash
pip install batchmark
```

## Usage

Define your commands in a YAML file and run `batchmark` against it:

```yaml
# commands.yaml
commands:
  - name: list files
    run: ls -la
  - name: disk usage
    run: du -sh .
  - name: python version
    run: python --version
```

```bash
batchmark run commands.yaml
```

**Example output:**

```
┌─────────────────┬──────────┬──────────┬──────────┐
│ Command         │ Min (ms) │ Max (ms) │ Avg (ms) │
├─────────────────┼──────────┼──────────┼──────────┤
│ list files      │   12.4   │   18.7   │   14.2   │
│ disk usage      │   45.1   │   52.3   │   47.8   │
│ python version  │   38.6   │   41.0   │   39.5   │
└─────────────────┴──────────┴──────────┴──────────┘
```

Export results to JSON or CSV with the `--output` flag:

```bash
batchmark run commands.yaml --output report.json
batchmark run commands.yaml --output report.csv --iterations 10
```

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `--iterations` | Number of times to run each command | `5` |
| `--output` | Export results to a file (`.json` or `.csv`) | None |
| `--quiet` | Suppress command stdout/stderr | False |

## License

MIT © batchmark contributors