"""Tests for batchmark.profile_report."""
import json
import pytest
from batchmark.runner import CommandResult
from batchmark.profile import ProfileSnapshot
from batchmark.profile_report import (
    attach_profiles,
    enrich_result_dict,
    format_json_with_profiles,
    format_table_with_profiles,
)


def make_result(cmd="echo hi", rc=0, duration=0.1):
    return CommandResult(command=cmd, returncode=rc, stdout="", stderr="", duration=duration, timed_out=False)


def make_snap(cmd="echo hi", wall=0.1, user=0.05, sys=0.01, rss=1024):
    return ProfileSnapshot(command=cmd, wall_time=wall, user_time=user, sys_time=sys, max_rss_kb=rss)


def test_attach_profiles_matches_by_command():
    r = make_result("ls")
    s = make_snap("ls")
    pairs = attach_profiles([r], [s])
    assert pairs[0][1] is s


def test_attach_profiles_missing_snap():
    r = make_result("ls")
    pairs = attach_profiles([r], [])
    assert pairs[0][1] is None


def test_attach_profiles_multiple():
    results = [make_result("ls"), make_result("pwd")]
    snaps = [make_snap("pwd"), make_snap("ls")]
    pairs = attach_profiles(results, snaps)
    assert pairs[0][1].command == "ls"
    assert pairs[1][1].command == "pwd"


def test_enrich_result_dict_adds_profile():
    d = {"command": "ls", "duration": 0.1}
    snap = make_snap("ls")
    enriched = enrich_result_dict(d, snap)
    assert "profile" in enriched
    assert enriched["profile"]["max_rss_kb"] == 1024


def test_enrich_result_dict_none_snap():
    d = {"command": "ls"}
    enriched = enrich_result_dict(d, None)
    assert enriched["profile"] is None


def test_format_json_with_profiles_valid_json():
    results = [make_result("echo hi")]
    snaps = [make_snap("echo hi")]
    output = format_json_with_profiles(results, snaps)
    data = json.loads(output)
    assert "results" in data
    assert data["results"][0]["profile"] is not None


def test_format_table_with_profiles_includes_section():
    results = [make_result("echo hi")]
    snaps = [make_snap("echo hi")]
    output = format_table_with_profiles(results, snaps)
    assert "Profile Summary" in output
    assert "echo hi" in output
