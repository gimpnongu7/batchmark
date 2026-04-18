"""Tests for batchmark.retry."""
import pytest
from unittest.mock import patch, MagicMock
from batchmark.retry import RetryConfig, RetryResult, should_retry, run_with_retry
from batchmark.runner import CommandResult


def make_result(returncode=0, timed_out=False, duration=0.1):
    return CommandResult(
        command="echo hi",
        returncode=returncode,
        stdout="",
        stderr="",
        duration=duration,
        timed_out=timed_out,
    )


def test_should_retry_on_failure():
    cfg = RetryConfig(retry_on_failure=True)
    assert should_retry(make_result(returncode=1), cfg) is True


def test_should_not_retry_success():
    cfg = RetryConfig()
    assert should_retry(make_result(returncode=0), cfg) is False


def test_should_retry_timeout():
    cfg = RetryConfig(retry_on_timeout=True)
    assert should_retry(make_result(timed_out=True), cfg) is True


def test_should_not_retry_timeout_disabled():
    cfg = RetryConfig(retry_on_timeout=False)
    assert should_retry(make_result(timed_out=True), cfg) is False


def test_run_with_retry_success_first_attempt():
    ok = make_result(returncode=0)
    with patch("batchmark.retry.run_command", return_value=ok) as mock_run:
        rr = run_with_retry("echo hi", cfg=RetryConfig(max_attempts=3, delay=0))
    assert rr.succeeded_on == 1
    assert rr.total_attempts == 1
    mock_run.assert_called_once()


def test_run_with_retry_succeeds_on_second():
    fail = make_result(returncode=1)
    ok = make_result(returncode=0)
    with patch("batchmark.retry.run_command", side_effect=[fail, ok]):
        with patch("batchmark.retry.time.sleep"):
            rr = run_with_retry("cmd", cfg=RetryConfig(max_attempts=3, delay=0.1))
    assert rr.succeeded_on == 2
    assert rr.total_attempts == 2


def test_run_with_retry_exhausted():
    fail = make_result(returncode=1)
    with patch("batchmark.retry.run_command", return_value=fail):
        with patch("batchmark.retry.time.sleep"):
            rr = run_with_retry("cmd", cfg=RetryConfig(max_attempts=3, delay=0))
    assert rr.succeeded_on is None
    assert rr.total_attempts == 3


def test_retry_result_final_is_last_attempt():
    results = [make_result(returncode=1), make_result(returncode=1), make_result(returncode=2)]
    with patch("batchmark.retry.run_command", side_effect=results):
        with patch("batchmark.retry.time.sleep"):
            rr = run_with_retry("cmd", cfg=RetryConfig(max_attempts=3, delay=0))
    assert rr.final.returncode == 2
