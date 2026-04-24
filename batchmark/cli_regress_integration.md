# CLI Regression Detection Integration

## Overview

The `regress` module compares a **baseline** run against a **current** run and
flags commands whose mean duration has worsened beyond a configurable threshold.

## Config keys (`regress` section)

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `threshold_pct` | float | `10.0` | Percent increase that triggers a regression flag |
| `threshold_abs` | float | `0.0` | Absolute delta (seconds) that triggers a flag; `0` disables |
| `min_baseline_runs` | int | `1` | Minimum baseline samples required before comparing |

## Example config

```yaml
commands:
  - echo hello
  - sleep 0.1

regress:
  threshold_pct: 15.0
  threshold_abs: 0.5
  min_baseline_runs: 2
```

## CLI usage

```bash
# Save a baseline
batchmark run --config config.yaml --export baseline.json

# Run again and compare
batchmark run --config config.yaml --regress-baseline baseline.json
```

## Output (table)

```
Command                                  Base(s)  Curr(s)    Delta    Pct% Flag   Reason
-----------------------------------------------------------------------
echo hello                                 0.010    0.025    0.015  150.0% REGR   150.0% > threshold 15.0%
sleep 0.1                                  0.102    0.103    0.001    1.0% ok     within threshold

Regression check: 1/2 command(s) regressed.
```

## Integration notes

- `detect_regressions(baseline, current, config)` accepts two lists of
  `CommandResult` objects and returns `List[RegressEntry]`.
- Commands present in `current` but absent from `baseline` are silently skipped
  (they cannot be compared).
- Both `threshold_pct` and `threshold_abs` are evaluated independently; either
  condition is sufficient to mark a regression.
