"""Tests for batchmark.relay_report."""
from __future__ import annotations

import json

import pytest

from batchmark.relay import RelayResponse
from batchmark.relay_report import (
    response_to_dict,
    format_relay_json,
    format_relay_table,
    relay_summary,
)


def make_resp(status=200, ok=True, body="ok"):
    return RelayResponse(status=status, ok=ok, body=body)


def test_response_to_dict_keys():
    d = response_to_dict(make_resp())
    assert set(d.keys()) == {"status", "ok", "body"}


def test_response_to_dict_values():
    d = response_to_dict(make_resp(status=404, ok=False, body="not found"))
    assert d["status"] == 404
    assert d["ok"] is False
    assert d["body"] == "not found"


def test_format_relay_json_valid():
    resps = [make_resp(200), make_resp(500, ok=False, body="err")]
    out = format_relay_json(resps)
    parsed = json.loads(out)
    assert len(parsed) == 2
    assert parsed[1]["status"] == 500


def test_format_relay_table_header():
    out = format_relay_table([make_resp()])
    assert "STATUS" in out
    assert "OK" in out


def test_format_relay_table_rows():
    resps = [make_resp(200), make_resp(503, ok=False, body="down")]
    out = format_relay_table(resps)
    assert "200" in out
    assert "503" in out
    assert "no" in out


def test_relay_summary_counts():
    resps = [make_resp(200), make_resp(200), make_resp(500, ok=False)]
    s = relay_summary(resps)
    assert s["total"] == 3
    assert s["succeeded"] == 2
    assert s["failed"] == 1


def test_relay_summary_all_ok():
    resps = [make_resp() for _ in range(4)]
    s = relay_summary(resps)
    assert s["failed"] == 0
