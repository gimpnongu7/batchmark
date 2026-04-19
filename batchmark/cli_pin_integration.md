# Pin Integration

The `pin` feature lets you force specific commands to run first or last
in the output ordering, regardless of their natural execution order.

## Config

```yaml
commands:
  - echo a
  - echo b
  - echo c

pin:
  first:
    - echo c
  last:
    - echo a
```

## Behaviour

- Commands listed under `pin.first` are moved to the front of the results list.
- Commands listed under `pin.last` are moved to the end.
- A command listed in both `first` and `last` is treated as `first`.
- Commands not present in the actual batch are silently ignored.
- All other commands retain their relative order in the middle.

## API

```python
from batchmark.pin import parse_pin_config, pin_results

cfg = parse_pin_config(raw_config)
ordered = pin_results(results, cfg)
```

## CLI usage

Pass a config file with a `pin` block and the runner will reorder results
before formatting output:

```
batchmark run --config sample_pin_config.yaml --format table
```
