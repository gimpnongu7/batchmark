"""Tests for the CLI entry point."""
import json
from pathlib import Path
import pytest

from batchmark.cli import main


@pytest.fixture()
def json_config(tmp_path: Path) -> Path:
    cfg = {
        "commands": [
            {"label": "echo", "cmd": "echo hello"},
            {"label": "true", "cmd": "true"},
        ]
    }
    p = tmp_path / "bench.json"
    p.write_text(json.dumps(cfg))
    return p


def test_cli_table_output(json_config, capsys):
    rc = main([str(json_config)])
    assert rc == 0
    captured = capsys.readouterr()
    assert "echo" in captured.out


def test_cli_json_output(json_config, capsys):
    rc = main([str(json_config), "--format", "json"])
    assert rc == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert len(data) == 2


def test_cli_write_to_file(json_config, tmp_path):
    out_file = tmp_path / "result.json"
    rc = main([str(json_config), "--format", "json", "--output", str(out_file)])
    assert rc == 0
    assert out_file.exists()
    data = json.loads(out_file.read_text())
    assert len(data) == 2


def test_cli_missing_config(tmp_path):
    rc = main([str(tmp_path / "nope.json")])
    assert rc == 1


def test_cli_empty_commands(tmp_path, capsys):
    cfg = tmp_path / "empty.json"
    cfg.write_text(json.dumps({"commands": []}))
    rc = main([str(cfg)])
    assert rc == 1
