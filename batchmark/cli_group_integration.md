# Group Integration Guide

## Overview

`batchmark.group` lets you bucket `CommandResult` lists by a field or custom
function and get per-group `BatchStats` automatically.

## Basic usage

```python
from batchmark.group import group_by, format_group_table

results = run_batch(commands)
groups = group_by(results, "status")
print(format_group_table(groups))
```

Sample output:

```
Group                          Count       Mean        Min        Max
----------------------------------------------------------------------
failure                            3      1.200      0.500      2.100
success                           12      0.843      0.210      3.400
```

## Grouping by command

```python
groups = group_by(results, "command")
for name, entry in groups.items():
    print(name, entry.stats.mean)
```

## Custom grouping

```python
from batchmark.group import group_by_fn

groups = group_by_fn(results, lambda r: "fast" if r.duration < 1.0 else "slow")
```

## CLI flag (planned)

```
batchmark run config.yaml --group-by status
batchmark run config.yaml --group-by command
```

When `--group-by` is provided the table output will be replaced by the grouped
summary table showing per-group statistics.
