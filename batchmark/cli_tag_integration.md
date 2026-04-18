# Tag Integration Guide

Tags let you group and filter benchmark results by logical categories (e.g. `io`, `cpu`, `fast`).

## Config Example

```yaml
commands:
  - echo hello
  - ls -la
  - pwd

tags:
  "echo hello": [io, fast]
  "ls -la": [io]
  "pwd": [fast]
```

## CLI Usage

Filter output to only commands matching a tag:

```bash
batchmark run config.yaml --tag io
```

Group summary by tag:

```bash
batchmark run config.yaml --group-by-tag
```

## API Usage

```python
from batchmark.tag import tag_results, filter_by_tag, group_by_tag

tagged = tag_results(results, config["tags"])
io_only = filter_by_tag(tagged, "io")
groups = group_by_tag(tagged)
```

## Notes

- A command with no entry in `tags` gets an empty tag list.
- A result can belong to multiple tags.
- `group_by_tag` returns a dict mapping tag -> list of `CommandResult`.
- `list_tags` returns a sorted list of all unique tags present.
