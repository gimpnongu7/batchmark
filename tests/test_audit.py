import pytest
from batchmark.runner import CommandResult
from batchmark.audit import AuditLog, AuditEntry, build_audit_log, merge_audit_logs


def make_result(cmd="echo hi", status="success", duration=0.5):
    return CommandResult(command=cmd, status=status, duration=duration, stdout="", stderr="", returncode=0)


def test_add_entry():
    log = AuditLog()
    r = make_result()
    log.add(r, run_index=0)
    assert len(log.entries) == 1
    assert log.entries[0].command == "echo hi"


def test_entry_note():
    log = AuditLog()
    r = make_result()
    log.add(r, run_index=1, note="baseline run")
    assert log.entries[0].note == "baseline run"
    assert log.entries[0].run_index == 1


def test_filter_by_status():
    log = AuditLog()
    log.add(make_result(status="success"), run_index=0)
    log.add(make_result(status="failure"), run_index=0)
    log.add(make_result(status="success"), run_index=0)
    assert len(log.filter_by_status("success")) == 2
    assert len(log.filter_by_status("failure")) == 1


def test_commands_deduped():
    log = AuditLog()
    log.add(make_result(cmd="echo a"), run_index=0)
    log.add(make_result(cmd="echo b"), run_index=0)
    log.add(make_result(cmd="echo a"), run_index=1)
    cmds = log.commands()
    assert cmds == ["echo a", "echo b"]


def test_build_audit_log():
    results = [make_result(cmd=f"cmd{i}") for i in range(3)]
    log = build_audit_log(results, run_index=2, note="test")
    assert len(log.entries) == 3
    assert all(e.run_index == 2 for e in log.entries)
    assert all(e.note == "test" for e in log.entries)


def test_merge_audit_logs():
    log_a = build_audit_log([make_result(cmd="a")], run_index=0)
    log_b = build_audit_log([make_result(cmd="b"), make_result(cmd="c")], run_index=1)
    merged = merge_audit_logs([log_a, log_b])
    assert len(merged.entries) == 3
