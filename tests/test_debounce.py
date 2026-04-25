import pytest
from batchmark.runner import CommandResult
from batchmark.debounce import (
    DebounceConfig,
    DebounceState,
    debounce_results,
    parse_debounce_config,
)


def make_result(command="echo hi", status="success", duration=0.1, start_time=0.0):
    return CommandResult(
        command=command,
        status=status,
        duration=duration,
        stdout="",
        stderr="",
        returncode=0,
        start_time=start_time,
    )


# ---------------------------------------------------------------------------
# parse_debounce_config
# ---------------------------------------------------------------------------

def test_parse_debounce_config_defaults():
    cfg = parse_debounce_config({})
    assert cfg.window == 0.5
    assert cfg.key == "command"
    assert cfg.keep == "last"


def test_parse_debounce_config_custom():
    cfg = parse_debounce_config({"window": 1.0, "key": "status", "keep": "first"})
    assert cfg.window == 1.0
    assert cfg.key == "status"
    assert cfg.keep == "first"


# ---------------------------------------------------------------------------
# debounce_results — keep last
# ---------------------------------------------------------------------------

def test_debounce_keep_last_within_window():
    results = [
        make_result(command="echo hi", duration=0.1, start_time=0.0),
        make_result(command="echo hi", duration=0.9, start_time=0.3),
    ]
    cfg = DebounceConfig(window=0.5, keep="last")
    out = debounce_results(results, cfg)
    assert len(out) == 1
    assert out[0].duration == 0.9


def test_debounce_keep_first_within_window():
    results = [
        make_result(command="echo hi", duration=0.1, start_time=0.0),
        make_result(command="echo hi", duration=0.9, start_time=0.3),
    ]
    cfg = DebounceConfig(window=0.5, keep="first")
    out = debounce_results(results, cfg)
    assert len(out) == 1
    assert out[0].duration == 0.1


def test_debounce_outside_window_keeps_both():
    results = [
        make_result(command="echo hi", start_time=0.0),
        make_result(command="echo hi", start_time=1.0),
    ]
    cfg = DebounceConfig(window=0.5, keep="last")
    out = debounce_results(results, cfg)
    assert len(out) == 2


def test_debounce_different_commands_not_merged():
    results = [
        make_result(command="echo a", start_time=0.0),
        make_result(command="echo b", start_time=0.1),
    ]
    cfg = DebounceConfig(window=0.5, keep="last")
    out = debounce_results(results, cfg)
    assert len(out) == 2


def test_debounce_key_by_status():
    results = [
        make_result(command="cmd1", status="success", start_time=0.0),
        make_result(command="cmd2", status="success", start_time=0.2),
    ]
    cfg = DebounceConfig(window=0.5, key="status", keep="first")
    out = debounce_results(results, cfg)
    # both share same status key, within window -> only one kept
    assert len(out) == 1
    assert out[0].command == "cmd1"


def test_debounce_empty_input():
    out = debounce_results([], DebounceConfig())
    assert out == []


def test_debounce_single_result_unchanged():
    r = make_result(start_time=0.0)
    out = debounce_results([r], DebounceConfig())
    assert len(out) == 1
    assert out[0] is r
