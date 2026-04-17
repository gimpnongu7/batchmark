"""Tests for batchmark.config."""
import json
from pathlib import Path
import pytest

from batchmark.config import load_config


@pytest.fixture()
def valid_json_config(tmp_path: Path) -> Path:
    data = {
        "timeout": 10,
        "commands": [
            {"label": "hello", "cmd": "echo hello"},
            {"cmd": "true"},
        ],
    }
    p = tmp_path / "config.json"
    p.write_text(json.dumps(data))
    return p


def test_load_json_config(valid_json_config):
    cfg = load_config(valid_json_config)
    assert cfg["timeout"] == 10
    assert len(cfg["commands"]) == 2


def test_load_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "ghost.json")


def test_load_unsupported_extension(tmp_path):
    p = tmp_path / "config.toml"
    p.write_text("[commands]")
    with pytest.raises(ValueError, match="Unsupported"):
        load_config(p)


def test_missing_commands_key(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"timeout": 5}))
    with pytest.raises(ValueError, match="commands"):
        load_config(p)


def test_command_missing_cmd_key(tmp_path):
    p = tmp_path / "bad2.json"
    p.write_text(json.dumps({"commands": [{"label": "oops"}]}))
    with pytest.raises(ValueError, match="cmd"):
        load_config(p)


def test_non_dict_top_level(tmp_path):
    p = tmp_path / "list.json"
    p.write_text(json.dumps(["echo hi"]))
    with pytest.raises(ValueError, match="mapping"):
        load_config(p)
