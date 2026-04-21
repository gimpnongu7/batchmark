import pytest
from batchmark.runner import CommandResult
from batchmark.heatmap import (
    HeatmapConfig,
    parse_heatmap_config,
    build_heatmap,
    format_heatmap_table,
    _BLOCKS,
)
from batchmark.heatmap_report import (
    cell_to_dict,
    format_heatmap_json,
    heatmap_summary,
    report_heatmap,
)
import json


def make_result(cmd: str, duration: float, status: str = "success") -> CommandResult:
    return CommandResult(command=cmd, duration=duration, status=status, stdout="", stderr="", returncode=0)


@pytest.fixture
def sample_results():
    return [
        make_result("echo a", 0.1),
        make_result("sleep 1", 1.0),
        make_result("sleep 2", 2.0),
        make_result("ls", 0.5),
        make_result("pwd", 0.05),
    ]


def test_parse_heatmap_config_defaults():
    cfg = parse_heatmap_config({})
    assert cfg.buckets == 5
    assert cfg.min_duration is None
    assert cfg.max_duration is None


def test_parse_heatmap_config_custom():
    cfg = parse_heatmap_config({"buckets": 3, "min_duration": 0.0, "max_duration": 5.0})
    assert cfg.buckets == 3
    assert cfg.min_duration == 0.0
    assert cfg.max_duration == 5.0


def test_build_heatmap_count(sample_results):
    cells = build_heatmap(sample_results, HeatmapConfig())
    assert len(cells) == len(sample_results)


def test_build_heatmap_symbols_valid(sample_results):
    cells = build_heatmap(sample_results, HeatmapConfig())
    for c in cells:
        assert c.symbol in _BLOCKS


def test_build_heatmap_hottest_is_slowest(sample_results):
    cells = build_heatmap(sample_results, HeatmapConfig())
    by_cmd = {c.command: c for c in cells}
    assert by_cmd["sleep 2"].intensity >= by_cmd["pwd"].intensity


def test_build_heatmap_empty():
    assert build_heatmap([], HeatmapConfig()) == []


def test_build_heatmap_zero_span():
    results = [make_result("a", 1.0), make_result("b", 1.0)]
    cells = build_heatmap(results, HeatmapConfig())
    assert all(c.intensity == cells[0].intensity for c in cells)


def test_format_heatmap_table_has_header(sample_results):
    cells = build_heatmap(sample_results, HeatmapConfig())
    table = format_heatmap_table(cells)
    assert "COMMAND" in table
    assert "HEAT" in table


def test_format_heatmap_table_empty():
    assert format_heatmap_table([]) == "(no results)"


def test_cell_to_dict_keys():
    r = make_result("echo hi", 0.3)
    cells = build_heatmap([r], HeatmapConfig())
    d = cell_to_dict(cells[0])
    assert set(d.keys()) == {"command", "duration", "status", "intensity", "symbol"}


def test_format_heatmap_json_valid(sample_results):
    cells = build_heatmap(sample_results, HeatmapConfig())
    data = json.loads(format_heatmap_json(cells))
    assert isinstance(data, list)
    assert len(data) == len(sample_results)


def test_heatmap_summary_hottest_coolest(sample_results):
    cells = build_heatmap(sample_results, HeatmapConfig())
    summary = heatmap_summary(cells)
    assert summary["total"] == len(sample_results)
    assert summary["hottest"]["command"] == "sleep 2"
    assert summary["coolest"]["command"] == "pwd"


def test_heatmap_summary_empty():
    s = heatmap_summary([])
    assert s["total"] == 0
    assert s["hottest"] is None


def test_report_heatmap_table(sample_results):
    out = report_heatmap(sample_results, HeatmapConfig(), fmt="table")
    assert "COMMAND" in out


def test_report_heatmap_json(sample_results):
    out = report_heatmap(sample_results, HeatmapConfig(), fmt="json")
    data = json.loads(out)
    assert len(data) == len(sample_results)
