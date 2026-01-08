import uuid

import pytest

from citrine.informatics.executions.predictor_evaluation import (
    PredictorEvaluation,
    PredictorEvaluationRequest,
    PredictorEvaluatorsResponse,
)
from citrine.informatics.predictor_evaluator import CrossValidationEvaluator
from citrine.informatics.predictor_evaluation_metrics import NDME
from citrine.informatics.predictor_evaluation_result import PredictorEvaluationResult
from citrine._rest.resource import PredictorRef
from tests.utils.session import FakeCall, FakeSession


@pytest.fixture
def cross_validation_evaluator():
    yield CrossValidationEvaluator(
        "foo",
        description="desc",
        responses={"dk"},
        n_folds=2,
        n_trials=5,
        metrics={NDME()},
    )


@pytest.fixture
def predictor_ref():
    yield PredictorRef(uuid.uuid4(), 4)


@pytest.fixture
def predictor_evaluators_response(cross_validation_evaluator):
    yield PredictorEvaluatorsResponse([cross_validation_evaluator])


@pytest.fixture
def predictor_evaluation_request(cross_validation_evaluator, predictor_ref):
    yield PredictorEvaluationRequest(
        evaluators=[cross_validation_evaluator],
        predictor_id=predictor_ref.uid,
        predictor_version=predictor_ref.version,
    )


@pytest.fixture
def predictor_evaluation(cross_validation_evaluator, predictor_ref):
    evaluation = PredictorEvaluation()
    evaluation.uid = uuid.uuid4()
    evaluation.evaluators = [cross_validation_evaluator]
    evaluation.predictor_id = predictor_ref.uid
    evaluation.predictor_version = predictor_ref.version
    evaluation.status = "SUCCEEDED"
    evaluation.status_description = "COMPLETED"
    yield evaluation


def test_predictor_evaluator_response(
    predictor_evaluators_response, cross_validation_evaluator
):
    assert predictor_evaluators_response.evaluators == [cross_validation_evaluator]


def test_predictor_evaluator_request(
    predictor_evaluation_request, cross_validation_evaluator, predictor_ref
):
    assert predictor_evaluation_request.evaluators == [cross_validation_evaluator]
    assert predictor_evaluation_request.predictor.dump() == predictor_ref.dump()


def test_predictor_evaluation(
    predictor_evaluation, cross_validation_evaluator, predictor_ref
):
    assert predictor_evaluation.evaluators == [cross_validation_evaluator]
    assert predictor_evaluation.evaluator_names == [cross_validation_evaluator.name]
    assert predictor_evaluation.predictor_id == predictor_ref.uid
    assert predictor_evaluation.predictor_version == predictor_ref.version
    assert predictor_evaluation.status == "SUCCEEDED"
    assert predictor_evaluation.status_description == "COMPLETED"
    assert predictor_evaluation.status_detail == []


def test_results(predictor_evaluation, example_cv_result_dict):
    session = FakeSession()
    predictor_evaluation._session = session
    predictor_evaluation.project_id = uuid.uuid4()

    session.set_response(example_cv_result_dict)

    results = predictor_evaluation["Example Evaluator"]

    expected_call = FakeCall(
        method="GET",
        path=f"/projects/{predictor_evaluation.project_id}/predictor-evaluations/{predictor_evaluation.uid}/results",
        params={"evaluator_name": "Example Evaluator"},
    )
    assert session.last_call == expected_call
    assert (
        results.evaluator
        == PredictorEvaluationResult.build(example_cv_result_dict).evaluator
    )


def test_results_invalid_type(predictor_evaluation):
    session = FakeSession()
    predictor_evaluation._session = session
    predictor_evaluation.project_id = uuid.uuid4()

    with pytest.raises(TypeError):
        predictor_evaluation[1]
