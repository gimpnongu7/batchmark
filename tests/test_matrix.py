import pytest
from unittest.mock import patch
from batchmark.matrix import (
    MatrixConfig, MatrixEntry, _expand_matrix, run_matrix, format_matrix_table
)
from batchmark.runner import CommandResult


def make_result(cmd="echo hi", status="success", duration=0.1):
    return CommandResult(command=cmd, status=status, duration=duration,
                        stdout="hi", stderr="", returncode=0)


def test_expand_matrix_single_var():
    combos = _expand_matrix({"env": ["dev", "prod"]})
    assert len(combos) == 2
    assert {"env": "dev"} in combos
    assert {"env": "prod"} in combos


def test_expand_matrix_two_vars():
    combos = _expand_matrix({"env": ["dev", "prod"], "region": ["us", "eu"]})
    assert len(combos) == 4


def test_expand_matrix_empty():
    combos = _expand_matrix({})
    assert combos == [{}]


def test_expand_matrix_single_value():
    combos = _expand_matrix({"x": [1]})
    assert combos == [{"x": 1}]


def test_run_matrix_entry_count():
    config = MatrixConfig(
        commands=["echo {env}", "ping {env}"],
        matrix={"env": ["dev", "prod"]},
    )
    fake = make_result()
    with patch("batchmark.matrix.run_command", return_value=fake):
        entries = run_matrix(config)
    assert len(entries) == 4  # 2 commands x 2 envs


def test_run_matrix_rendered_command():
    config = MatrixConfig(
        commands=["echo {name}"],
        matrix={"name": ["alice"]},
    )
    fake = make_result()
    with patch("batchmark.matrix.run_command", return_value=fake):
        entries = run_matrix(config)
    assert entries[0].rendered_command == "echo alice"


def test_run_matrix_variables_stored():
    config = MatrixConfig(
        commands=["echo {x}"],
        matrix={"x": [42]},
    )
    fake = make_result()
    with patch("batchmark.matrix.run_command", return_value=fake):
        entries = run_matrix(config)
    assert entries[0].variables == {"x": 42}


def test_format_matrix_table_header():
    entries = [
        MatrixEntry(command_template="echo {env}", variables={"env": "dev"},
                    result=make_result(cmd="echo dev", duration=0.05))
    ]
    table = format_matrix_table(entries)
    assert "COMMAND" in table
    assert "VARS" in table
    assert "STATUS" in table
    assert "DURATION" in table


def test_format_matrix_table_row_content():
    entries = [
        MatrixEntry(command_template="echo {env}", variables={"env": "prod"},
                    result=make_result(cmd="echo prod", status="success", duration=0.12))
    ]
    table = format_matrix_table(entries)
    assert "echo prod" in table
    assert "env=prod" in table
    assert "success" in table
