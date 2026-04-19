import pytest
from batchmark.runner import CommandResult
from batchmark.annotate import (
    AnnotatedResult,
    annotate_results,
    filter_by_annotation,
    group_by_annotation,
    list_annotation_keys,
)


def make_result(cmd: str, status: str = "success", duration: float = 1.0) -> CommandResult:
    return CommandResult(command=cmd, status=status, duration=duration, stdout="", stderr="", returncode=0)


@pytest.fixture
def results():
    return [
        make_result("echo hello"),
        make_result("sleep 1"),
        make_result("ls -la"),
    ]


@pytest.fixture
def annotation_map():
    return {
        "echo hello": {"team": "infra", "env": "prod"},
        "sleep 1": {"team": "dev", "env": "staging"},
    }


def test_annotate_results_assigns_annotations(results, annotation_map):
    annotated = annotate_results(results, annotation_map)
    assert annotated[0].annotations == {"team": "infra", "env": "prod"}
    assert annotated[1].annotations == {"team": "dev", "env": "staging"}


def test_annotate_results_empty_for_unknown(results, annotation_map):
    annotated = annotate_results(results, annotation_map)
    assert annotated[2].annotations == {}


def test_annotate_results_preserves_command(results, annotation_map):
    annotated = annotate_results(results, annotation_map)
    assert annotated[0].result.command == "echo hello"


def test_get_returns_value(results, annotation_map):
    annotated = annotate_results(results, annotation_map)
    assert annotated[0].get("team") == "infra"


def test_get_returns_default_for_missing(results, annotation_map):
    annotated = annotate_results(results, annotation_map)
    assert annotated[2].get("team", "unknown") == "unknown"


def test_filter_by_annotation(results, annotation_map):
    annotated = annotate_results(results, annotation_map)
    filtered = filter_by_annotation(annotated, "team", "infra")
    assert len(filtered) == 1
    assert filtered[0].result.command == "echo hello"


def test_filter_by_annotation_no_match(results, annotation_map):
    annotated = annotate_results(results, annotation_map)
    filtered = filter_by_annotation(annotated, "team", "qa")
    assert filtered == []


def test_group_by_annotation(results, annotation_map):
    annotated = annotate_results(results, annotation_map)
    groups = group_by_annotation(annotated, "team")
    assert "infra" in groups
    assert "dev" in groups
    assert len(groups["infra"]) == 1


def test_group_by_annotation_unknown_key(results, annotation_map):
    annotated = annotate_results(results, annotation_map)
    groups = group_by_annotation(annotated, "nonexistent")
    assert "" in groups
    assert len(groups[""]) == 3


def test_list_annotation_keys(results, annotation_map):
    annotated = annotate_results(results, annotation_map)
    keys = list_annotation_keys(annotated)
    assert keys == ["env", "team"]
