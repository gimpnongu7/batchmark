import pytest
from batchmark.runner import CommandResult
from batchmark.bucket import (
    BucketConfig, BucketResult, bucket_results, parse_bucket_config, _default_labels
)


def make_result(cmd: str, duration: float, status: str = "success") -> CommandResult:
    return CommandResult(command=cmd, duration=duration, status=status, stdout="", stderr="", returncode=0)


@pytest.fixture
def sample_results():
    return [
        make_result("a", 0.2),
        make_result("b", 0.7),
        make_result("c", 1.1),
        make_result("d", 2.5),
        make_result("e", 0.9),
    ]


def test_default_labels_count():
    labels = _default_labels([0.5, 1.0])
    assert len(labels) == 3


def test_default_labels_content():
    labels = _default_labels([1.0])
    assert "1.0" in labels[0]
    assert "+inf" in labels[1]


def test_bucket_config_sorts_boundaries():
    cfg = BucketConfig(boundaries=[2.0, 0.5, 1.0])
    assert cfg.boundaries == [0.5, 1.0, 2.0]


def test_bucket_config_label_mismatch_raises():
    with pytest.raises(ValueError):
        BucketConfig(boundaries=[1.0], labels=["only_one"])


def test_bucket_results_count(sample_results):
    cfg = BucketConfig(boundaries=[0.5, 1.0, 2.0])
    buckets = bucket_results(sample_results, cfg)
    assert sum(b.count for b in buckets) == len(sample_results)


def test_bucket_results_first_bucket(sample_results):
    cfg = BucketConfig(boundaries=[0.5, 1.0, 2.0])
    buckets = bucket_results(sample_results, cfg)
    # 0.2 only
    assert buckets[0].count == 1
    assert buckets[0].results[0].command == "a"


def test_bucket_results_middle_bucket(sample_results):
    cfg = BucketConfig(boundaries=[0.5, 1.0, 2.0])
    buckets = bucket_results(sample_results, cfg)
    # 0.7 and 0.9
    assert buckets[1].count == 2


def test_bucket_results_last_bucket(sample_results):
    cfg = BucketConfig(boundaries=[0.5, 1.0, 2.0])
    buckets = bucket_results(sample_results, cfg)
    # 2.5
    assert buckets[3].count == 1


def test_mean_duration_none_for_empty():
    b = BucketResult(label="x", lower=0.0, upper=1.0)
    assert b.mean_duration is None


def test_mean_duration_calculated(sample_results):
    cfg = BucketConfig(boundaries=[0.5, 1.0, 2.0])
    buckets = bucket_results(sample_results, cfg)
    mid = buckets[1]  # 0.7, 0.9
    assert abs(mid.mean_duration - 0.8) < 1e-9


def test_parse_bucket_config_basic():
    cfg = parse_bucket_config({"boundaries": [1.0, 2.0]})
    assert cfg.boundaries == [1.0, 2.0]
    assert len(cfg.labels) == 3


def test_parse_bucket_config_custom_labels():
    cfg = parse_bucket_config({"boundaries": [1.0], "labels": ["fast", "slow"]})
    assert cfg.labels == ["fast", "slow"]
