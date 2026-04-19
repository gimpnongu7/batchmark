"""Tests for batchmark.relay."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from batchmark.relay import (
    RelayConfig,
    RelayResponse,
    _result_to_dict,
    relay_result,
    relay_batch,
    parse_relay_config,
)
from batchmark.runner import CommandResult


def make_result(cmd="echo hi", rc=0, duration=0.1, timed_out=False):
    return CommandResult(
        command=cmd, returncode=rc, stdout="hi", stderr="", duration=duration, timed_out=timed_out
    )


def test_result_to_dict_keys():
    d = _result_to_dict(make_result())
    assert set(d.keys()) == {"command", "returncode", "duration", "stdout", "stderr", "timed_out"}


def test_result_to_dict_values():
    r = make_result(cmd="ls", rc=1, duration=0.5)
    d = _result_to_dict(r)
    assert d["command"] == "ls"
    assert d["returncode"] == 1
    assert d["duration"] == 0.5


def _mock_urlopen(status=200, body=b"ok"):
    cm = MagicMock()
    cm.__enter__ = lambda s: s
    cm.__exit__ = MagicMock(return_value=False)
    cm.status = status
    cm.read.return_value = body
    return cm


def test_relay_result_success():
    cfg = RelayConfig(url="http://example.com/ingest")
    with patch("urllib.request.urlopen", return_value=_mock_urlopen(200, b"received")):
        resp = relay_result(make_result(), cfg)
    assert resp.ok is True
    assert resp.status == 200
    assert resp.body == "received"


def test_relay_result_http_error_warn():
    import urllib.error
    cfg = RelayConfig(url="http://example.com/ingest", on_failure="warn")
    with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(
        url="", code=500, msg="Server Error", hdrs=None, fp=None
    )):
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            resp = relay_result(make_result(), cfg)
            assert len(w) == 1
    assert resp.ok is False
    assert resp.status == 500


def test_relay_result_raises_on_failure():
    import urllib.error
    cfg = RelayConfig(url="http://example.com/ingest", on_failure="raise")
    with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(
        url="", code=503, msg="Unavailable", hdrs=None, fp=None
    )):
        with pytest.raises(RuntimeError, match="relay failed"):
            relay_result(make_result(), cfg)


def test_relay_batch_returns_all():
    cfg = RelayConfig(url="http://example.com/ingest")
    results = [make_result(f"cmd{i}") for i in range(3)]
    with patch("urllib.request.urlopen", return_value=_mock_urlopen()):
        responses = relay_batch(results, cfg)
    assert len(responses) == 3
    assert all(r.ok for r in responses)


def test_parse_relay_config_none_when_missing():
    assert parse_relay_config({}) is None


def test_parse_relay_config_full():
    data = {"relay": {"url": "http://host/ep", "method": "PUT", "timeout": 3.0, "on_failure": "ignore"}}
    cfg = parse_relay_config(data)
    assert cfg.url == "http://host/ep"
    assert cfg.method == "PUT"
    assert cfg.timeout == 3.0
    assert cfg.on_failure == "ignore"
