import pytest
from batchmark.runner import CommandResult
from batchmark.outlier import OutlierConfig, OutlierResult, detect_outliers, parse_outlier_config


def make_result(cmd: str, duration: float, rc: int = 0) -> CommandResult:
    return CommandResult(command=cmd, duration=duration, returncode=rc, stdout="", stderr="")


@pytest.fixture
def normal_results():
    return [
        make_result("cmd_a", 1.0),
        make_result("cmd_b", 1.1),
        make_result("cmd_c", 1.05),
        make_result("cmd_d", 1.2),
        make_result("cmd_e", 15.0),  # outlier
    ]


def test_detect_outliers_iqr_finds_spike(normal_results):
    results = detect_outliers(normal_results)
    assert len(results) == 1
    assert results[0].result.command == "cmd_e"


def test_detect_outliers_iqr_score_positive(normal_results):
    results = detect_outliers(normal_results)
    assert results[0].score > 0


def test_detect_outliers_reason_contains_fence(normal_results):
    results = detect_outliers(normal_results)
    assert "IQR fence" in results[0].reason


def test_detect_outliers_zscore(normal_results):
    cfg = OutlierConfig(method="zscore", zscore_threshold=2.0)
    results = detect_outliers(normal_results, config=cfg)
    assert any(o.result.command == "cmd_e" for o in results)


def test_detect_outliers_zscore_reason(normal_results):
    cfg = OutlierConfig(method="zscore", zscore_threshold=2.0)
    results = detect_outliers(normal_results, config=cfg)
    assert "z-score" in results[0].reason


def test_detect_outliers_excludes_failures_by_default():
    results = [
        make_result("ok1", 1.0),
        make_result("ok2", 1.1),
        make_result("ok3", 1.05),
        make_result("fail", 99.0, rc=1),
    ]
    found = detect_outliers(results)
    assert all(o.result.returncode == 0 for o in found)


def test_detect_outliers_includes_failures_when_configured():
    results = [
        make_result("ok1", 1.0),
        make_result("ok2", 1.1),
        make_result("ok3", 1.05),
        make_result("fail", 99.0, rc=1),
    ]
    cfg = OutlierConfig(include_failures=True)
    found = detect_outliers(results, config=cfg)
    assert any(o.result.returncode == 1 for o in found)


def test_detect_outliers_too_few_results():
    results = [make_result("a", 1.0), make_result("b", 2.0)]
    assert detect_outliers(results) == []


def test_parse_outlier_config_defaults():
    cfg = parse_outlier_config({})
    assert cfg.method == "iqr"
    assert cfg.iqr_factor == 1.5
    assert cfg.zscore_threshold == 2.0
    assert cfg.include_failures is False


def test_parse_outlier_config_custom():
    cfg = parse_outlier_config({"method": "zscore", "zscore_threshold": 3.0, "include_failures": True})
    assert cfg.method == "zscore"
    assert cfg.zscore_threshold == 3.0
    assert cfg.include_failures is True
