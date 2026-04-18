# CLI Environment Variable Integration

This document describes how `batchmark.env` integrates with the CLI and config system.

## Config File Usage

Add an `env` section to your YAML or JSON config:

```yaml
commands:
  - echo $MY_VAR
  - python script.py

env:
  inherit: true
  vars:
    MY_VAR: hello
    API_URL: http://localhost:8080
```

- `inherit` (default: `true`): whether to inherit the current shell environment.
- `vars`: key-value pairs injected into every command's environment.

## CLI Overrides

Pass `--env KEY=VALUE` flags to override or add variables at runtime:

```bash
batchmark run config.yaml --env MY_VAR=world --env DEBUG=1
```

CLI overrides take highest precedence:
1. OS environment (if `inherit: true`)
2. `env.vars` from config
3. `--env` CLI flags

## Programmatic Usage

```python
from batchmark.env import EnvConfig, build_env, parse_env_list

cfg = EnvConfig(base={"FOO": "bar"}, inherit=True)
overrides = parse_env_list(["FOO=overridden", "EXTRA=1"])
env = build_env(cfg, overrides=overrides)
```

## Notes

- Environment variables apply to **all** commands in the batch.
- Per-command env overrides are not yet supported.
