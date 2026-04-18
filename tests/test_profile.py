"""Tests for batchmark.profile."""
import pytest
from unittest.mock import MagicMock
from batchmark.profile import (
    ProfileSnapshot,
    snapshot_from_rusage,
    profile_to_dict,
    format_profile_table,
)


def make_snapshot(command="echo hi", wall=1.0, user=0.8, sys=0.1, rss=4096):
    return ProfileSnapshot(
        command=command,
        wall_time=wall,
        user_time=user,
        sys_time=sys,
        max_rss_kb=rss,
    )


def test_cpu_time():
    s = make_snapshot(user=0.5, sys=0.2)
    assert round(s.cpu_time, 6) == pytest.approx(0.7)


def test_cpu_efficiency():
    s = make_snapshot(wall=1.0, user=0.8, sys=0.2)
    assert s.cpu_efficiency == pytest.approx(1.0)


def test_cpu_efficiency_zero_wall():
    s = make_snapshot(wall=0.0)
    assert s.cpu_efficiency is None


def test_snapshot_from_rusage():
    usage = MagicMock()
    usage.ru_utime = 0.3
    usage.ru_stime = 0.1
    usage.ru_maxrss = 2048
    snap = snapshot_from_rusage("ls", 0.5, usage)
    assert snap.command == "ls"
    assert snap.wall_time == pytest.approx(0.5)
    assert snap.user_time == pytest.approx(0.3)
    assert snap.max_rss_kb == 2048


def test_profile_to_dict_keys():
    s = make_snapshot()
    d = profile_to_dict(s)
    assert set(d.keys()) == {"command", "wall_time", "user_time", "sys_time", "cpu_time", "cpu_efficiency", "max_rss_kb"}


def test_profile_to_dict_values():
    s = make_snapshot(command="sleep 1", wall=1.0, user=0.0, sys=0.0, rss=512)
    d = profile_to_dict(s)
    assert d["command"] == "sleep 1"
    assert d["max_rss_kb"] == 512


def test_format_profile_table_contains_command():
    snaps = [make_snapshot(command="echo hi"), make_snapshot(command="ls -la")]
    table = format_profile_table(snaps)
    assert "echo hi" in table
    assert "ls -la" in table


def test_format_profile_table_has_header():
    table = format_profile_table([make_snapshot()])
    assert "Wall" in table
    assert "RSS" in table


def test_format_profile_table_empty():
    table = format_profile_table([])
    assert "Wall" in table
