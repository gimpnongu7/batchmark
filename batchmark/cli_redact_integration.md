# Redact Integration

The `redact` module scrubs sensitive values from commands, output, and environment
before they appear in reports or are written to disk.

## Config

Add a `redact` section to your JSON/YAML config:

```yaml
redact:
  placeholder: "***"
  patterns:
    - 'password=\S+'
    - 'token=[^\s]+'
  env_keys:
    - AWS_SECRET_ACCESS_KEY
    - API_TOKEN
```

## CLI usage

Redaction is applied automatically when `--redact` flag is passed:

```
batchmark run config.yaml --redact
```

## How it works

1. `load_redact_config(raw)` reads the `redact` section from the loaded config.
2. `redact_result_dict(d, cfg)` is called on every result dict before formatting.
3. `redact_env(env, cfg)` is called before passing the environment to subprocesses
   so secrets never appear in logs.

## Notes

- Patterns are Python `re` patterns applied via `re.sub`.
- `env_keys` matching is case-insensitive.
- The original `CommandResult` objects are **not** mutated; redaction happens only
  on the serialised dicts used for output.
