"""Tests for citrine.informatics.descriptors."""

import json

import pytest

from citrine.informatics.predictor_evaluation_metrics import *
from citrine.informatics.predictor_evaluation_result import (
    PredictedVsActualCategoricalPoint,
    PredictedVsActualRealPoint,
    PredictorEvaluationResult,
)
from citrine.informatics.predictor_evaluator import CrossValidationEvaluator, HoldoutSetEvaluator


@pytest.fixture
def example_cv_result(example_cv_result_dict):
    return PredictorEvaluationResult.build(example_cv_result_dict)


@pytest.fixture
def example_holdout_result(example_holdout_result_dict):
    return PredictorEvaluationResult.build(example_holdout_result_dict)


def test_indexing(example_cv_result, example_holdout_result):
    assert example_cv_result.responses == {"saltiness", "salt?"}
    assert example_holdout_result.responses == {"sweetness"}
    assert example_cv_result.metrics == {RMSE(), PVA(), F1()}
    assert example_holdout_result.metrics == {RMSE()}
    assert set(example_cv_result["salt?"]) == {repr(F1()), repr(PVA())}
    assert set(example_cv_result) == {"salt?", "saltiness"}
    assert set(example_holdout_result["sweetness"]) == {repr(RMSE())}
    assert set(example_holdout_result) == {"sweetness"}


def test_cv_serde(example_cv_result, example_cv_result_dict):
    round_trip = PredictorEvaluationResult.build(json.loads(json.dumps(example_cv_result_dict)))
    assert example_cv_result.evaluator == round_trip.evaluator


def test_holdout_serde(example_holdout_result, example_holdout_result_dict):
    round_trip = PredictorEvaluationResult.build(
        json.loads(json.dumps(example_holdout_result_dict))
    )
    assert example_holdout_result.evaluator == round_trip.evaluator


def test_ev_evaluator(example_cv_result, example_cv_evaluator_dict):
    args = example_cv_evaluator_dict
    del args["type"]
    expected = CrossValidationEvaluator(**args)
    assert expected.responses == set(example_cv_evaluator_dict["responses"])
    assert example_cv_result.evaluator == expected
    assert example_cv_result.evaluator != 0  # make sure eq does something for mismatched classes


def test_holdout_set_evaluator(example_holdout_result, example_holdout_evaluator_dict):
    args = example_holdout_evaluator_dict
    del args["type"]
    expected = HoldoutSetEvaluator(**args)
    assert expected.responses == set(example_holdout_evaluator_dict["responses"])
    assert example_holdout_result.evaluator == expected
    # make sure eq does something for mismatched classes
    assert example_holdout_result.evaluator != 0


def test_check_rmse(example_cv_result, example_rmse_metrics):
    ex_cv_saltiness = example_cv_result["saltiness"]
    assert ex_cv_saltiness["rmse"].mean == example_rmse_metrics["mean"]
    assert ex_cv_saltiness[RMSE()].standard_error == example_rmse_metrics["standard_error"]
    assert ex_cv_saltiness[RMSE()] != 0  # Verify eq method does something
    with pytest.raises(TypeError):
        _ = ex_cv_saltiness[0]


def test_real_pva(example_cv_result, example_real_pva_metrics):
    args = example_real_pva_metrics["value"][0]
    expected = PredictedVsActualRealPoint.build(args)
    pva = example_cv_result["saltiness"]["predicted_vs_actual"]
    assert list(pva) == pva.value  # __iter__
    assert pva[0].predicted == expected.predicted  # __getitem__
    assert pva[0].actual == expected.actual


def test_categorical_pva(example_cv_result, example_categorical_pva_metrics):
    args = example_categorical_pva_metrics["value"][0]
    expected = PredictedVsActualCategoricalPoint.build(args)
    pva = example_cv_result["salt?"]["predicted_vs_actual"]
    assert list(pva) == pva.value  # __iter__
    assert pva[0].predicted == expected.predicted  # __getitem__
    assert pva[0].actual == expected.actual
