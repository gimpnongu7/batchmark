# Progress Bar Integration

Batchmark can display a live progress bar while running commands.

## CLI Flags

```
--progress            Enable progress bar (default: on when TTY)
--no-progress         Disable progress bar
--progress-width N    Width of the bar in characters (default: 30)
```

## How It Works

A `ProgressConfig` is built from CLI args and passed to `make_progress_callback`.
The returned callback is invoked after each command completes inside `run_batch`.

```python
from batchmark.progress import ProgressConfig, make_progress_callback
from batchmark.runner import run_batch

cfg = ProgressConfig(enabled=True, bar_width=40)
callback = make_progress_callback(total=len(commands), cfg=cfg)
results = run_batch(commands, on_complete=callback)
```

## Output Example

```
[##########--------------------]  33% (1/3)  2.1s  cmd: echo hello
[####################----------]  67% (2/3)  4.3s  cmd: sleep 1
[##############################] 100% (3/3)  5.1s  cmd: ls -la
```

The bar is written to `stderr` so it does not interfere with `--output` file
or piped `stdout`.

## Config File

```yaml
progress:
  enabled: true
  bar_width: 30
  show_elapsed: true
```
