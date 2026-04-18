import pytest
from batchmark.runner import CommandResult
from batchmark.tag import (
    tag_results,
    filter_by_tag,
    group_by_tag,
    list_tags,
    TaggedResult,
)


def make_result(command: str, status: str = "success", duration: float = 0.1):
    return CommandResult(
        command=command,
        status=status,
        duration=duration,
        stdout="",
        stderr="",
        returncode=0 if status == "success" else 1,
    )


@pytest.fixture
def results():
    return [
        make_result("echo hello"),
        make_result("ls -la"),
        make_result("pwd"),
    ]


@pytest.fixture
def tag_map():
    return {
        "echo hello": ["io", "fast"],
        "ls -la": ["io"],
        "pwd": ["fast"],
    }


def test_tag_results_assigns_tags(results, tag_map):
    tagged = tag_results(results, tag_map)
    assert len(tagged) == 3
    echo_tagged = next(t for t in tagged if t.result.command == "echo hello")
    assert "io" in echo_tagged.tags
    assert "fast" in echo_tagged.tags


def test_tag_results_empty_tags_for_unknown(results):
    tagged = tag_results(results, {})
    for t in tagged:
        assert t.tags == []


def test_filter_by_tag(results, tag_map):
    tagged = tag_results(results, tag_map)
    io_results = filter_by_tag(tagged, "io")
    commands = [t.result.command for t in io_results]
    assert "echo hello" in commands
    assert "ls -la" in commands
    assert "pwd" not in commands


def test_filter_by_tag_no_match(results, tag_map):
    tagged = tag_results(results, tag_map)
    assert filter_by_tag(tagged, "nonexistent") == []


def test_group_by_tag(results, tag_map):
    tagged = tag_results(results, tag_map)
    groups = group_by_tag(tagged)
    assert set(groups.keys()) == {"io", "fast"}
    assert len(groups["io"]) == 2
    assert len(groups["fast"]) == 2


def test_list_tags(results, tag_map):
    tagged = tag_results(results, tag_map)
    tags = list_tags(tagged)
    assert tags == ["fast", "io"]


def test_list_tags_empty():
    assert list_tags([]) == []
