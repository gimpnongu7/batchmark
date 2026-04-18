# Retry Integration

The `retry` module adds automatic retry support for flaky or intermittently failing commands.

## Usage

```python
from batchmark.retry import RetryConfig, run_with_retry

cfg = RetryConfig(max_attempts=3, delay=0.5, retry_on_failure=True, retry_on_timeout=True)
result = run_with_retry("curl https://example.com", timeout=10.0, cfg=cfg)

print(f"Succeeded on attempt: {result.succeeded_on}")
print(f"Total attempts: {result.total_attempts}")
print(f"Final return code: {result.final.returncode}")
```

## Config Options

| Field | Default | Description |
|---|---|---|
| `max_attempts` | `3` | Maximum number of tries |
| `delay` | `0.5` | Seconds to wait between retries |
| `retry_on_failure` | `True` | Retry when returncode != 0 |
| `retry_on_timeout` | `True` | Retry when command times out |

## RetryResult Fields

- `final` — the last `CommandResult` (successful or not)
- `attempts` — list of all `CommandResult` objects in order
- `succeeded_on` — attempt number that succeeded, or `None` if all failed

## CLI Integration (planned)

Add `--retries` and `--retry-delay` flags to `batchmark/cli.py`:

```
batchmark run config.yaml --retries 3 --retry-delay 1.0
```

Each command in the batch would use `run_with_retry` instead of `run_command`.
The final `CommandResult` is passed downstream to reporting and export as usual.
