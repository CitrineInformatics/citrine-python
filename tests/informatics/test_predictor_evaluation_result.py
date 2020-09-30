"""Tests for citrine.informatics.descriptors."""
import json
import pytest
from citrine.informatics.predictor_evaluation_metrics import *
from citrine.informatics.predictor_evaluation_result import PredictorEvaluationResult, CrossValidationResult, \
    RealMetricValue, RealPredictedVsActual, CategoricalPredictedVsActual


@pytest.fixture
def example_result(example_result_dict):
    return PredictorEvaluationResult.build(example_result_dict)


def test_indexing(example_result):
    assert example_result.responses == {"saltiness", "salt?"}
    assert example_result.metrics == {RMSE(), PVA(), F1()}
    assert set(example_result["salt?"]) == {repr(F1()), repr(PVA())}


def test_serde(example_result, example_result_dict):
    round_trip = PredictorEvaluationResult.build(json.loads(json.dumps(example_result_dict)))
    assert example_result.evaluator == round_trip.evaluator


def test_check_rmse(example_result, example_rmse_metrics):
    expected = RealMetricValue(
        mean=example_rmse_metrics["mean"],
        standard_error=example_rmse_metrics["standard_error"]
    )
    assert expected != 0  # check eq method does something
    assert example_result["saltiness"]["rmse"] == expected
    assert example_result["saltiness"][RMSE()] == expected
    with pytest.raises(TypeError):
        foo = example_result["saltiness"][0]


def test_real_pva(example_result, example_real_pva_metrics):
    args = example_real_pva_metrics["value"][0]
    del args["type"]
    expected = RealPredictedVsActual(**args)
    assert example_result["saltiness"]["predicted_vs_actual"][0].predicted == expected.predicted
    assert next(iter(example_result["saltiness"]["predicted_vs_actual"])).actual == expected.actual


def test_categorical_pva(example_result, example_categorical_pva_metrics):
    args = example_categorical_pva_metrics["value"][0]
    del args["type"]
    expected = CategoricalPredictedVsActual(**args)
    assert example_result["salt?"]["predicted_vs_actual"][0].predicted == expected.predicted
    assert next(iter(example_result["salt?"]["predicted_vs_actual"])).actual == expected.actual
