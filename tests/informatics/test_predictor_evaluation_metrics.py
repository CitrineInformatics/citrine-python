"""Tests for citrine.informatics.descriptors."""
import json
import logging

import pytest
from citrine.informatics.predictor_evaluation_metrics import *


@pytest.fixture(params=[
    (RMSE(), "rmse", "RMSE"),
    (RSquared(), "R^2", "R^2"),
    (NDME(), "ndme", "NDME"),
    (StandardRMSE(), "standardized_rmse", "Standardized RMSE"),
    (PVA(), "predicted_vs_actual", "Predicted vs Actual"),
    (F1(), "f1", "F1 Score"),
    (AreaUnderROC(), "area_under_roc", "Area Under the ROC"),
    (CoverageProbability(coverage_level=0.123), "coverage_probability_0.123", "Coverage Probability (0.123)")
])
def metric(request):
    return request.param


def test_deser_from_parent(metric):
    # Serialize and deserialize the metrics, making sure they are round-trip serializable
    data = metric[0].dump()
    deserialized = PredictorEvaluationMetric.build(data)
    assert deserialized != "foo"  # check eq on wrong type
    assert metric[0] == deserialized


def test_string_rep(metric):
    """String representations of metrics should match our expectation"""
    assert str(metric[0]) == metric[2]
    assert repr(metric[0]) == metric[1]


def test_to_json(metric):
    """Make sure we can dump the metrics to json"""
    json_str = json.dumps(metric[0].dump())
    deser = PredictorEvaluationMetric.build(json.loads(json_str))
    assert deser == metric[0]


def test_coverage_levels(caplog):
    assert CoverageProbability(coverage_level="0.123")._level_str == "0.123"
    with caplog.at_level(logging.WARNING):
        caplog.clear()
        assert CoverageProbability(coverage_level="0.1234")._level_str == "0.123"
        assert any(r.levelno == logging.WARNING for r in caplog.records)
    assert CoverageProbability(coverage_level=0.123)._level_str == "0.123"
    with caplog.at_level(logging.WARNING):
        caplog.clear()
        assert CoverageProbability(coverage_level=0.1234)._level_str == "0.123"
        assert any(r.levelno == logging.WARNING for r in caplog.records)

    with pytest.raises(TypeError):
        CoverageProbability(coverage_level=123)

    with pytest.raises(ValueError):
        CoverageProbability(coverage_level="foo bar")

    with pytest.raises(ValueError):
        CoverageProbability(coverage_level=123.0)

    with pytest.raises(ValueError):
        CoverageProbability(coverage_level="68.2")

    with caplog.at_level(logging.WARNING):
        caplog.clear()
        CoverageProbability(coverage_level=".1111")
        assert any(r.levelno == logging.WARNING for r in caplog.records)
