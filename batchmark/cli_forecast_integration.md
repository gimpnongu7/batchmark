# Forecast Integration Guide

The `forecast` module predicts future run durations based on historical
`CommandResult` data collected across multiple runs.

## Overview

- **`forecast(results, cfg)`** — groups results by command, applies a sliding
  window, computes mean duration, and labels each command with a trend:
  `stable`, `improving`, or `degrading`.
- **`ForecastConfig`** — controls window size and the threshold that determines
  when a trend is significant.

## CLI Usage

```bash
# Run a batch and save results, then forecast from a history file
batchmark run config.yaml --output history.json
batchmark forecast history.json --window 5 --format table
```

## Config Options

```yaml
forecast:
  window: 5            # number of most-recent runs per command to consider
  trend_threshold: 0.10  # fractional change required to label a trend
```

## Output Formats

### Table
```
Command                                  Samples   Mean(s)  Predicted(s) Trend
------------------------------------------------------------------------
echo hello                                     5    0.0120        0.0120 stable
sleep 1                                        3    1.0050        1.0050 degrading
```

### JSON
```json
[
  {
    "command": "echo hello",
    "sample_count": 5,
    "mean_duration": 0.012,
    "predicted_next": 0.012,
    "trend": "stable"
  }
]
```

## Notes

- Only successful results should be passed to `forecast()` for meaningful
  predictions; filter with `filter_results` first if needed.
- When fewer than 2 samples exist in the window, the trend defaults to
  `"stable"`.
- Combine with `baseline` to compare predictions against recorded baselines.
