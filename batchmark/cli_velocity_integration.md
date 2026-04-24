# Velocity Integration Guide

The `velocity` module tracks **throughput** — how many commands per second are
being executed — across a result list, both cumulatively and over a rolling
window.

## Config keys (inline or via YAML)

```yaml
velocity:
  window: 10        # rolling window size (default: 10)
  min_samples: 2    # minimum results before computing velocity (default: 2)
```

## Programmatic usage

```python
from batchmark.runner import run_batch
from batchmark.velocity import compute_velocity, parse_velocity_config
from batchmark.velocity_report import format_velocity_table, velocity_summary

results = run_batch(["sleep 0.1", "echo hi", "ls /tmp"])
cfg = parse_velocity_config({"window": 5, "min_samples": 2})
entries = compute_velocity(results, cfg)

print(format_velocity_table(entries))
print(velocity_summary(entries))
```

## CLI flag (planned)

```
batchmark run config.yaml --velocity --velocity-window 5
```

When enabled, the velocity table is appended after the standard timing report.

## Output columns

| Column | Description |
|---|---|
| `#` | Zero-based index in result list |
| `Command` | Shell command string |
| `Duration` | Wall-clock time for this command (s) |
| `Rolling v/s` | Commands per second over the last N results |
| `Cumul v/s` | Commands per second since the start |
| `Accel` | `up` if rolling > cumulative, `down` otherwise |

## Notes

- Velocity is `None` until `min_samples` results have accumulated.
- A rolling velocity higher than cumulative indicates the batch is
  **speeding up** (e.g. later commands are faster).
- Use `format_velocity_json` for machine-readable output suitable for
  piping into dashboards or storage.
