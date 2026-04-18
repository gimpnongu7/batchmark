import pytest
from batchmark.truncate import (
    TruncateConfig,
    truncate_string,
    truncate_result_dict,
    truncate_results,
    parse_truncate_config,
)


def make_result(stdout="hello world", stderr=""):
    return {"command": "echo hi", "stdout": stdout, "stderr": stderr, "status": "success"}


def test_truncate_string_no_limit():
    assert truncate_string("hello", None) == "hello"


def test_truncate_string_within_limit():
    assert truncate_string("hello", 10) == "hello"


def test_truncate_string_exact_limit():
    assert truncate_string("hello", 5) == "hello"


def test_truncate_string_exceeds_limit():
    result = truncate_string("hello world", 8)
    assert result == "hello..."
    assert len(result) == 8


def test_truncate_string_custom_ellipsis():
    result = truncate_string("abcdef", 5, "--")
    assert result == "abc--"


def test_truncate_string_tiny_limit():
    result = truncate_string("hello", 2)
    assert result == ".."


def test_truncate_result_dict_stdout():
    cfg = TruncateConfig(max_stdout=5)
    r = make_result(stdout="hello world")
    out = truncate_result_dict(r, cfg)
    assert out["stdout"] == "he..."


def test_truncate_result_dict_stderr():
    cfg = TruncateConfig(max_stderr=6)
    r = make_result(stderr="error details here")
    out = truncate_result_dict(r, cfg)
    assert out["stderr"] == "err..."


def test_truncate_result_dict_does_not_mutate():
    cfg = TruncateConfig(max_stdout=4)
    r = make_result(stdout="long output")
    truncate_result_dict(r, cfg)
    assert r["stdout"] == "long output"


def test_truncate_result_dict_no_limits():
    cfg = TruncateConfig()
    r = make_result(stdout="anything", stderr="stuff")
    out = truncate_result_dict(r, cfg)
    assert out["stdout"] == "anything"
    assert out["stderr"] == "stuff"


def test_truncate_results_list():
    cfg = TruncateConfig(max_stdout=5)
    results = [make_result(stdout="hello world"), make_result(stdout="hi")]
    out = truncate_results(results, cfg)
    assert out[0]["stdout"] == "he..."
    assert out[1]["stdout"] == "hi"


def test_parse_truncate_config_defaults():
    cfg = parse_truncate_config({})
    assert cfg.max_stdout is None
    assert cfg.max_stderr is None
    assert cfg.ellipsis == "..."


def test_parse_truncate_config_full():
    raw = {"truncate": {"max_stdout": 200, "max_stderr": 100, "ellipsis": "~~"}}
    cfg = parse_truncate_config(raw)
    assert cfg.max_stdout == 200
    assert cfg.max_stderr == 100
    assert cfg.ellipsis == "~~"
