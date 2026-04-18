# Timeout Configuration Integration

Batchmark supports fine-grained timeout control via the `timeouts` section in your config file.

## Config Example

```yaml
commands:
  - echo hello
  - sleep 5
  - ls -la

timeouts:
  default: 30
  global_budget: 120
  per_command:
    sleep 5: 3
    ls -la: 5
```

## Fields

| Field | Type | Description |
|---|---|---|
| `default` | float | Timeout (seconds) applied to any command without a specific override. Default: `30.0`. |
| `per_command` | dict | Map of command string → timeout override in seconds. |
| `global_budget` | float | Optional total wall-clock budget for the entire batch run. |

## Behaviour

- Each command's effective timeout is `min(per_command or default, remaining_global_budget)`.
- Once the global budget is exhausted, remaining commands time out immediately.
- Commands that exceed their timeout are recorded with `status="timeout"`.

## CLI Integration

Timeout config is loaded automatically from your config file and passed through `parse_timeout_config`. No extra CLI flags are required.

```bash
batchmark run --config sample_config.yaml
```
