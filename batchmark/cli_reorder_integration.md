# Reorder Integration

The `reorder` module lets you control the presentation order of results
by pinning specific commands to the front (or back) of the output.

## Config

```yaml
reorder:
  priority:
    - "make test"
    - "make lint"
  reverse: false
  stable: true
```

## CLI Usage

```bash
batchmark run config.yaml --reorder-priority "make test" "make lint"
batchmark run config.yaml --reorder-reverse
```

## Behaviour

- Commands listed in `priority` are moved to the front in declared order.
- Remaining commands keep their original relative order (`stable: true`).
- `reverse: true` flips the entire final list after priority sorting.
- `move_to_back` is available programmatically to demote commands.

## Example

```python
from batchmark.reorder import reorder_results, ReorderConfig

cfg = ReorderConfig(priority=["make test"])
ordered = reorder_results(results, cfg)
```
