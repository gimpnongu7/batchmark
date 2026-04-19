# Checkpoint Integration

Checkpoints let you save progress mid-batch and resume if a run is interrupted.

## Config

Add a `checkpoint` block to your YAML/JSON config:

```yaml
checkpoint:
  path: .batchmark_checkpoint.json
  resume: true
  auto_save: true
```

## CLI flags

| Flag | Description |
|------|-------------|
| `--checkpoint PATH` | Path to checkpoint file |
| `--no-resume` | Ignore existing checkpoint, re-run all commands |

## Behaviour

1. On start, if a checkpoint file exists and `resume: true`, already-completed commands are skipped.
2. After each command completes, the checkpoint file is updated (when `auto_save: true`).
3. On clean completion the checkpoint file is removed automatically.

## Example

```bash
# Start a run — interrupted after 3 commands
batchmark run sample_config.yaml --checkpoint .cp.json

# Resume from where it stopped
batchmark run sample_config.yaml --checkpoint .cp.json
```

## Notes

- The checkpoint file stores full `CommandResult` data so reports include all runs.
- Use `--no-resume` to force a clean run while keeping the checkpoint path for new output.
