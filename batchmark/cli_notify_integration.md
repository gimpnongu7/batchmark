# Notify Integration

The `notify` module fires notification events after a batch run completes,
allowing users to receive summaries or failure alerts.

## Config Options

```yaml
notify:
  on_complete: true
  on_failure: true
  min_failures: 1
```

## CLI Usage

Notifications are triggered automatically at the end of a run when a
`notify` block is present in the config. Output goes to stdout by default.

```
batchmark run sample_config.yaml
# [batchmark notify] [run] Batch complete: 4 commands, 3 passed, 1 failed, avg 0.42s
# [batchmark notify] [run] Batch finished with 1 failure(s) out of 4 commands (total time: 1.68s)
```

## Custom Handlers

Programmatic use allows injecting a custom handler:

```python
from batchmark.notify import NotifyConfig, notify

cfg = NotifyConfig(
    on_complete=True,
    on_failure=True,
    handler=lambda label, event: send_slack(event.message)
)
notify(cfg, stats, label="nightly-bench")
```

## NotifyEvent Fields

| Field   | Type        | Description                        |
|---------|-------------|------------------------------------|
| kind    | str         | `'complete'` or `'failure'`        |
| stats   | BatchStats  | Full stats for the batch run       |
| message | str         | Human-readable notification string |
