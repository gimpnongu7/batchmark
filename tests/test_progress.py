import io
import time
from batchmark.progress import (
    ProgressConfig,
    ProgressState,
    render_progress,
    make_progress_callback,
    _render_bar,
)


def test_percent_zero():
    s = ProgressState(total=0)
    assert s.percent == 1.0


def test_percent_partial():
    s = ProgressState(total=10)
    s.completed = 3
    assert abs(s.percent - 0.3) < 1e-9


def test_render_bar_full():
    s = ProgressState(total=4)
    s.completed = 4
    bar = _render_bar(s, width=10)
    assert "100%" in bar
    assert "4/4" in bar
    assert "-" not in bar.split("]")[0]


def test_render_bar_empty():
    s = ProgressState(total=4)
    bar = _render_bar(s, width=10)
    assert "0%" in bar
    assert "#" not in bar.split("]")[0]


def test_render_progress_shows_elapsed():
    s = ProgressState(total=2)
    cfg = ProgressConfig(show_elapsed=True)
    out = render_progress(s, cfg)
    assert "s" in out


def test_render_progress_no_elapsed():
    s = ProgressState(total=2)
    cfg = ProgressConfig(show_elapsed=False)
    out = render_progress(s, cfg)
    assert out.endswith("%" + f" ({s.completed}/{s.total})") or "s" not in out.split("]")[1]


def test_callback_disabled():
    buf = io.StringIO()
    cfg = ProgressConfig(enabled=False, stream=buf)
    cb = make_progress_callback(3, cfg)
    cb("echo hello")
    assert buf.getvalue() == ""


def test_callback_writes_progress():
    buf = io.StringIO()
    cfg = ProgressConfig(enabled=True, stream=buf, show_elapsed=False)
    cb = make_progress_callback(2, cfg)
    cb("echo a")
    cb("echo b")
    output = buf.getvalue()
    assert "1/2" in output
    assert "2/2" in output
    assert output.endswith("\n")


def test_callback_increments():
    buf = io.StringIO()
    cfg = ProgressConfig(enabled=True, stream=buf, show_elapsed=False)
    cb = make_progress_callback(5, cfg)
    for i in range(3):
        cb(f"cmd {i}")
    assert "3/5" in buf.getvalue()
