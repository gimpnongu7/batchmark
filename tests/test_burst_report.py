import json
import pytest
from batchmark.runner import CommandResult
from batchmark.burst import BurstEntry, BurstConfig, detect_bursts
from batchmark.burst_report import (
    entry_to_dict,
    format_burst_json,
    format_burst_table,
    burst_summary,
)


def make_result(cmd: str, duration: float = 0.1, status: str = "success") -> CommandResult:
    return CommandResult(command=cmd, duration=duration, status=status, stdout="", stderr="", returncode=0)


def make_entry(cmd: str, window_count: int = 0, throttled: bool = False, cooldown: float = 0.0) -> BurstEntry:
    return BurstEntry(
        result=make_result(cmd),
        window_count=window_count,
        throttled=throttled,
        cooldown_applied=cooldown,
    )


@pytest.fixture
def entries():
    return [
        make_entry("cmd_a", window_count=1, throttled=False),
        make_entry("cmd_b", window_count=3, throttled=True, cooldown=0.5),
        make_entry("cmd_c", window_count=2, throttled=False),
    ]


def test_entry_to_dict_keys(entries):
    d = entry_to_dict(entries[0])
    assert set(d.keys()) == {"command", "duration", "status", "window_count", "throttled", "cooldown_applied"}


def test_entry_to_dict_throttled_true(entries):
    d = entry_to_dict(entries[1])
    assert d["throttled"] is True
    assert d["cooldown_applied"] == pytest.approx(0.5)


def test_entry_to_dict_throttled_false(entries):
    d = entry_to_dict(entries[0])
    assert d["throttled"] is False
    assert d["cooldown_applied"] == pytest.approx(0.0)


def test_format_burst_json_valid(entries):
    out = format_burst_json(entries)
    parsed = json.loads(out)
    assert isinstance(parsed, list)
    assert len(parsed) == 3


def test_format_burst_json_has_command(entries):
    out = format_burst_json(entries)
    parsed = json.loads(out)
    assert parsed[0]["command"] == "cmd_a"


def test_format_burst_table_header(entries):
    table = format_burst_table(entries)
    assert "COMMAND" in table
    assert "THROTTLED" in table
    assert "COOLDOWN" in table


def test_format_burst_table_summary_line(entries):
    table = format_burst_table(entries)
    assert "Throttled: 1" in table
    assert "Total: 3" in table


def test_burst_summary_counts(entries):
    s = burst_summary(entries)
    assert s["total"] == 3
    assert s["throttled_count"] == 1
    assert s["total_cooldown_seconds"] == pytest.approx(0.5)


def test_burst_summary_no_throttle():
    e = [make_entry(f"cmd{i}") for i in range(4)]
    s = burst_summary(e)
    assert s["throttled_count"] == 0
    assert s["total_cooldown_seconds"] == pytest.approx(0.0)
