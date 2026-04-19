import io
from unittest.mock import patch, MagicMock
from batchmark.progress import ProgressConfig, make_progress_callback, ProgressState, render_progress


def _run_fake_batch(commands, callback):
    """Simulate run_batch calling callback after each command."""
    for cmd in commands:
        callback(cmd)


def test_full_run_produces_complete_bar():
    commands = ["echo a", "echo b", "echo c"]
    buf = io.StringIO()
    cfg = ProgressConfig(enabled=True, stream=buf, show_elapsed=False, bar_width=10)
    cb = make_progress_callback(len(commands), cfg)
    _run_fake_batch(commands, cb)
    output = buf.getvalue()
    assert "3/3" in output
    assert "100%" in output
    assert output.endswith("\n")


def test_partial_run_shows_correct_count():
    buf = io.StringIO()
    cfg = ProgressConfig(enabled=True, stream=buf, show_elapsed=False)
    cb = make_progress_callback(10, cfg)
    _run_fake_batch(["cmd1", "cmd2"], cb)
    assert "2/10" in buf.getvalue()


def test_disabled_produces_no_output():
    buf = io.StringIO()
    cfg = ProgressConfig(enabled=False, stream=buf)
    cb = make_progress_callback(5, cfg)
    _run_fake_batch(["echo x", "echo y"], cb)
    assert buf.getvalue() == ""


def test_long_command_truncated_in_output():
    buf = io.StringIO()
    cfg = ProgressConfig(enabled=True, stream=buf, show_elapsed=False)
    long_cmd = "echo " + "a" * 100
    cb = make_progress_callback(1, cfg)
    cb(long_cmd)
    line = buf.getvalue()
    # each line should not be excessively long due to truncation at 40 chars
    display_cmd_part = line.split("cmd: ")[1].strip()
    assert len(display_cmd_part) <= 40


def test_progress_state_elapsed_increases():
    import time
    s = ProgressState(total=1)
    time.sleep(0.05)
    assert s.elapsed >= 0.04


def test_render_progress_format():
    s = ProgressState(total=4)
    s.completed = 2
    cfg = ProgressConfig(show_elapsed=False)
    out = render_progress(s, cfg)
    assert "50%" in out
    assert "2/4" in out
