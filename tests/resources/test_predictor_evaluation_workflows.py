import uuid

import pytest

from citrine.informatics.workflows import PredictorEvaluationWorkflow
from citrine.resources.predictor_evaluation_workflow import PredictorEvaluationWorkflowCollection
from tests.utils.session import FakeSession, FakeCall


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def collection(session) -> PredictorEvaluationWorkflowCollection:
    return PredictorEvaluationWorkflowCollection(
        project_id=uuid.uuid4(),
        session=session,
    )


@pytest.fixture
def workflow(collection: PredictorEvaluationWorkflowCollection, predictor_evaluation_workflow_dict) -> PredictorEvaluationWorkflow:
    return collection.build(predictor_evaluation_workflow_dict)


def test_basic_methods(workflow, collection):
    assert "PredictorEvaluationWorkflow" in str(workflow)
    assert workflow.evaluators[0].name == "Example evaluator"
