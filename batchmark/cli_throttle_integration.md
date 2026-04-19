# Throttle Integration

The `throttle` module lets you slow down command dispatch to avoid overwhelming
shared resources (CI agents, remote APIs, rate-limited services).

## Config keys

```yaml
throttle:
  inter_command_delay: 0.5   # seconds to wait between each command
  burst: 3                   # run N commands before inserting a delay
  max_concurrency: 1         # reserved for future parallel support
```

## CLI flags (planned)

| Flag | Description |
|------|-------------|
| `--throttle-delay SEC` | Override inter-command delay |
| `--throttle-burst N`   | Override burst size |

## Behaviour

- Commands always run sequentially (concurrency > 1 is a no-op for now).
- With `burst: 0` (default) a delay is inserted between **every** command.
- With `burst: N` the delay is inserted every *N* commands (i.e. at index
  `N`, `2N`, `3N`, …), allowing short bursts without pausing.
- The first command is **never** delayed.

## Example

```python
from batchmark.throttle import ThrottleConfig, run_throttled
from batchmark.runner import run_command

cfg = ThrottleConfig(inter_command_delay=1.0, burst=5)
results = run_throttled(commands, cfg, run_command)
```
