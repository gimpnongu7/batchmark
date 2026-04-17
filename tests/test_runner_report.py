import pytest
from batchmark.runner import run_command, run_batch, CommandResult
from batchmark.report import results_to_dict, format_json, format_table
import json


def test_run_command_success():
    result = run_command("echo hello")
    assert result.success
    assert result.exit_code == 0
    assert "hello" in result.stdout
    assert result.duration_seconds >= 0


def test_run_command_failure():
    result = run_command("exit 1")
    assert not result.success
    assert result.exit_code == 1


def test_run_command_timeout():
    result = run_command("sleep 10", timeout=0.1)
    assert not result.success
    assert result.exit_code == -1
    assert "timed out" in result.stderr


def test_run_batch_returns_all():
    results = run_batch(["echo a", "echo b", "echo c"])
    assert len(results) == 3
    assert all(r.success for r in results)


def test_results_to_dict_summary():
    results = run_batch(["echo ok", "exit 2"])
    data = results_to_dict(results)
    assert data["summary"]["total"] == 2
    assert data["summary"]["passed"] == 1
    assert data["summary"]["failed"] == 1
    assert len(data["commands"]) == 2


def test_format_json_valid():
    results = run_batch(["echo hi"])
    output = format_json(results)
    parsed = json.loads(output)
    assert "summary" in parsed
    assert "commands" in parsed


def test_format_table_contains_headers():
    results = run_batch(["echo hi"])
    table = format_table(results)
    assert "COMMAND" in table
    assert "STATUS" in table
    assert "DURATION" in table
    assert "OK" in table
