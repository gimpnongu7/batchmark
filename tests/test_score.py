import pytest
from batchmark.runner import CommandResult
from batchmark.score import (
    ScoreConfig, score_result, score_results, parse_score_config, _grade
)
from batchmark.score_report import scored_to_dict, format_score_json, format_score_table
import json


def make_result(command="echo hi", status="success", duration=1.0):
    return CommandResult(command=command, status=status, duration=duration,
                         returncode=0, stdout="", stderr="")


def test_grade_boundaries():
    assert _grade(95) == "A"
    assert _grade(80) == "B"
    assert _grade(65) == "C"
    assert _grade(45) == "D"
    assert _grade(20) == "F"


def test_score_fast_success():
    cfg = ScoreConfig(max_duration=10.0)
    r = make_result(duration=0.1)
    sr = score_result(r, cfg)
    assert sr.score > 90
    assert sr.grade == "A"


def test_score_slow_success():
    cfg = ScoreConfig(max_duration=5.0)
    r = make_result(duration=5.0)
    sr = score_result(r, cfg)
    assert sr.score == 0.0


def test_score_failure_penalty():
    cfg = ScoreConfig(max_duration=10.0, penalty_failure=50.0)
    r = make_result(status="failure", duration=0.0)
    sr = score_result(r, cfg)
    assert sr.score == 50.0


def test_score_timeout_penalty():
    cfg = ScoreConfig(max_duration=10.0, penalty_timeout=30.0)
    r = make_result(status="timeout", duration=0.0)
    sr = score_result(r, cfg)
    assert sr.score == 70.0


def test_score_clamped_to_zero():
    cfg = ScoreConfig(max_duration=1.0, penalty_failure=100.0)
    r = make_result(status="failure", duration=2.0)
    sr = score_result(r, cfg)
    assert sr.score == 0.0


def test_score_results_returns_all():
    results = [make_result(f"cmd{i}") for i in range(5)]
    scored = score_results(results)
    assert len(scored) == 5


def test_parse_score_config():
    raw = {"max_duration": 20.0, "penalty_failure": 40.0, "weight_duration": 0.5}
    cfg = parse_score_config(raw)
    assert cfg.max_duration == 20.0
    assert cfg.penalty_failure == 40.0
    assert cfg.weight_duration == 0.5


def test_scored_to_dict_keys():
    r = make_result()
    sr = score_results([r])[0]
    d = scored_to_dict(sr)
    assert set(d.keys()) == {"command", "status", "duration", "score", "grade"}


def test_format_score_json_valid():
    results = [make_result("cmd1"), make_result("cmd2", duration=3.0)]
    scored = score_results(results)
    out = format_score_json(scored)
    data = json.loads(out)
    assert len(data) == 2
    assert "score" in data[0]


def test_format_score_table_header():
    scored = score_results([make_result()])
    table = format_score_table(scored)
    assert "Command" in table
    assert "Grade" in table
    assert "Mean score" in table


def test_format_score_table_empty():
    assert format_score_table([]) == "No results."
