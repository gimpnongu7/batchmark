import pytest
from batchmark.notify import (
    NotifyConfig, NotifyEvent, build_message, should_notify, notify
)
from batchmark.stats import BatchStats


def make_stats(total=5, passed=4, failed=1, total_duration=3.0, avg_duration=0.6,
               median_duration=0.5, min_duration=0.1, max_duration=1.2):
    return BatchStats(
        total=total, passed=passed, failed=failed,
        total_duration=total_duration, avg_duration=avg_duration,
        median_duration=median_duration, min_duration=min_duration,
        max_duration=max_duration,
    )


def test_build_message_complete():
    stats = make_stats()
    msg = build_message("complete", stats)
    assert "5 commands" in msg
    assert "4 passed" in msg
    assert "1 failed" in msg


def test_build_message_failure():
    stats = make_stats()
    msg = build_message("failure", stats)
    assert "1 failure" in msg
    assert "5 commands" in msg


def test_should_notify_complete():
    cfg = NotifyConfig(on_complete=True)
    assert should_notify(cfg, make_stats(failed=0), "complete") is True


def test_should_not_notify_complete_disabled():
    cfg = NotifyConfig(on_complete=False)
    assert should_notify(cfg, make_stats(), "complete") is False


def test_should_notify_failure_threshold_met():
    cfg = NotifyConfig(on_failure=True, min_failures=1)
    assert should_notify(cfg, make_stats(failed=2), "failure") is True


def test_should_not_notify_failure_below_threshold():
    cfg = NotifyConfig(on_failure=True, min_failures=3)
    assert should_notify(cfg, make_stats(failed=1), "failure") is False


def test_notify_fires_events():
    received = []
    def handler(label, event):
        received.append((label, event))

    cfg = NotifyConfig(on_complete=True, on_failure=True, min_failures=1, handler=handler)
    stats = make_stats(failed=1)
    events = notify(cfg, stats, label="test-run")
    assert len(events) == 2
    kinds = {e.kind for e in events}
    assert kinds == {"complete", "failure"}
    assert all(label == "test-run" for label, _ in received)


def test_notify_no_failure_event_when_zero_failures():
    received = []
    cfg = NotifyConfig(on_complete=True, on_failure=True, min_failures=1,
                       handler=lambda l, e: received.append(e))
    stats = make_stats(failed=0, passed=5)
    events = notify(cfg, stats)
    assert all(e.kind != "failure" for e in events)
