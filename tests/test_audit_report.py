import json
import pytest
from batchmark.runner import CommandResult
from batchmark.audit import build_audit_log
from batchmark.audit_report import entry_to_dict, format_audit_json, format_audit_table, audit_summary


def make_result(cmd="echo hi", status="success", duration=1.0):
    return CommandResult(command=cmd, status=status, duration=duration, stdout="", stderr="", returncode=0)


@pytest.fixture
def log():
    results = [
        make_result(cmd="cmd1", status="success", duration=0.5),
        make_result(cmd="cmd2", status="failure", duration=1.5),
    ]
    return build_audit_log(results, run_index=0, note="ci")


def test_entry_to_dict_keys(log):
    d = entry_to_dict(log.entries[0])
    assert set(d.keys()) == {"command", "status", "duration", "timestamp", "run_index", "note"}


def test_entry_to_dict_values(log):
    d = entry_to_dict(log.entries[0])
    assert d["command"] == "cmd1"
    assert d["status"] == "success"
    assert d["note"] == "ci"


def test_format_audit_json_valid(log):
    out = format_audit_json(log)
    parsed = json.loads(out)
    assert len(parsed) == 2
    assert parsed[0]["command"] == "cmd1"


def test_format_audit_table_header(log):
    out = format_audit_table(log)
    assert "Command" in out
    assert "Status" in out
    assert "Duration" in out


def test_format_audit_table_empty():
    from batchmark.audit import AuditLog
    out = format_audit_table(AuditLog())
    assert "No audit entries" in out


def test_audit_summary(log):
    s = audit_summary(log)
    assert s["total"] == 2
    assert s["passed"] == 1
    assert s["failed"] == 1
    assert s["mean_duration"] == pytest.approx(1.0, rel=1e-3)
