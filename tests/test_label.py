"""Tests for batchmark.label."""
import pytest
from batchmark.runner import CommandResult
from batchmark.label import (
    LabeledResult,
    label_results,
    filter_by_label,
    group_by_label,
    list_label_keys,
    labeled_to_dict,
)


def make_result(command="echo hi", status="success", duration=0.5):
    return CommandResult(command=command, status=status, duration=duration, stdout="", stderr="", returncode=0)


@pytest.fixture
def results():
    return [
        make_result("echo hi"),
        make_result("sleep 1"),
        make_result("ls /tmp"),
    ]


@pytest.fixture
def label_map():
    return {
        "echo hi": {"env": "prod", "team": "infra"},
        "sleep 1": {"env": "staging", "team": "infra"},
        "ls /tmp": {"env": "prod", "team": "platform"},
    }


def test_label_results_assigns_labels(results, label_map):
    labeled = label_results(results, label_map)
    assert labeled[0].labels == {"env": "prod", "team": "infra"}


def test_label_results_empty_for_unknown(results):
    labeled = label_results(results, {})
    for lr in labeled:
        assert lr.labels == {}


def test_filter_by_label_returns_matching(results, label_map):
    labeled = label_results(results, label_map)
    prod = filter_by_label(labeled, "env", "prod")
    assert len(prod) == 2
    commands = [lr.result.command for lr in prod]
    assert "echo hi" in commands
    assert "ls /tmp" in commands


def test_filter_by_label_no_match(results, label_map):
    labeled = label_results(results, label_map)
    result = filter_by_label(labeled, "env", "dev")
    assert result == []


def test_group_by_label(results, label_map):
    labeled = label_results(results, label_map)
    groups = group_by_label(labeled, "team")
    assert set(groups.keys()) == {"infra", "platform"}
    assert len(groups["infra"]) == 2
    assert len(groups["platform"]) == 1


def test_list_label_keys(results, label_map):
    labeled = label_results(results, label_map)
    keys = list_label_keys(labeled)
    assert keys == ["env", "team"]


def test_labeled_to_dict(results, label_map):
    labeled = label_results(results, label_map)
    d = labeled_to_dict(labeled[0])
    assert d["command"] == "echo hi"
    assert d["labels"] == {"env": "prod", "team": "infra"}
    assert "duration" in d
    assert "status" in d
