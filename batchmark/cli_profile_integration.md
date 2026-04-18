# Profile Integration

The `profile` module adds CPU and memory usage snapshots alongside timing results.

## Usage

Add `--profile` flag to the CLI run command:

```bash
batchmark run config.yaml --profile
batchmark run config.yaml --profile --format table
```

## Config

No extra config keys required. Profiling is opt-in via CLI flag.

## Output Fields

| Field | Description |
|---|---|
| `wall_time` | Elapsed real time (seconds) |
| `user_time` | User-space CPU time |
| `sys_time` | Kernel CPU time |
| `cpu_time` | `user_time + sys_time` |
| `cpu_efficiency` | `cpu_time / wall_time` |
| `max_rss_kb` | Peak resident set size (KB) |

## JSON output

When `--format json` is used, each result gains a `profile` key:

```json
{
  "command": "sleep 0.1",
  "duration": 0.101,
  "status": "success",
  "profile": {
    "wall_time": 0.101,
    "cpu_time": 0.002,
    "cpu_efficiency": 0.0198,
    "max_rss_kb": 1024
  }
}
```

## Notes

- RSS is sampled via `resource.getrusage(RUSAGE_CHILDREN)` after each command.
- On macOS, `ru_maxrss` is in bytes; on Linux it is in kilobytes. Normalisation is platform-dependent.
- Profiling adds negligible overhead (~microseconds per command).
