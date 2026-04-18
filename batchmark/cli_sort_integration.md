# Sort Integration Notes

## CLI flags (planned)

Add the following flags to `build_parser()` in `cli.py`:

```
--sort-by   {duration,command,returncode,status}  Sort results (default: duration)
--sort-desc                                        Sort descending (default: ascending)
--top N                                            Show only top-N results after sorting
```

## Usage example

```bash
# Show the 3 slowest commands
batchmark run config.yaml --sort-by duration --sort-desc --top 3

# Sort alphabetically by command name
batchmark run config.yaml --sort-by command
```

## Integration snippet

```python
from batchmark.sort import sort_results, top_n

results = run_batch(commands, timeout=args.timeout)

if args.top:
    results = top_n(results, n=args.top, key=args.sort_by,
                    reverse=args.sort_desc)
elif args.sort_by:
    results = sort_results(results, key=args.sort_by,
                           reverse=args.sort_desc)
```
