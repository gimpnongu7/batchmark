# Label Integration Guide

Labels allow attaching arbitrary key-value metadata to commands for filtering and grouping results.

## Config Example

```yaml
commands:
  - echo hi
  - sleep 1
  - ls /tmp

labels:
  "echo hi":
    env: prod
    team: infra
  "sleep 1":
    env: staging
    team: infra
  "ls /tmp":
    env: prod
    team: platform
```

## CLI Flags

```
--label-filter KEY=VALUE   Only show results where label KEY equals VALUE
--label-group KEY          Group output by label KEY
--show-labels              Include label columns in table output
```

## Usage Examples

```bash
# Filter to prod only
batchmark run config.yaml --label-filter env=prod

# Group output by team
batchmark run config.yaml --label-group team

# Show labels in table
batchmark run config.yaml --show-labels
```

## Programmatic Usage

```python
from batchmark.label import label_results, filter_by_label, group_by_label

labeled = label_results(results, label_map)
prod_results = filter_by_label(labeled, "env", "prod")
groups = group_by_label(labeled, "team")
```
