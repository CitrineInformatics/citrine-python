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
def workflow(collection: PredictorEvaluationWorkflowCollection,
             predictor_evaluation_workflow_dict) -> PredictorEvaluationWorkflow:
    return collection.build(predictor_evaluation_workflow_dict)


def test_basic_methods(workflow, collection):
    assert "PredictorEvaluationWorkflow" in str(workflow)
    assert workflow.evaluators[0].name == "Example evaluator"


def test_archive(workflow, collection):
    collection.archive(workflow.uid)
    expected_path = '/projects/{}/predictor-evaluation-workflows/archive'.format(collection.project_id)
    assert collection.session.last_call == FakeCall(method='PUT', path=expected_path,
                                                    json={"module_uid": str(workflow.uid)})


def test_restore(workflow, collection):
    collection.restore(workflow.uid)
    expected_path = '/projects/{}/predictor-evaluation-workflows/restore'.format(collection.project_id)
    assert collection.session.last_call == FakeCall(method='PUT', path=expected_path,
                                                    json={"module_uid": str(workflow.uid)})


def test_delete(collection):
    with pytest.raises(NotImplementedError):
        collection.delete(uuid.uuid4())


def test_create_default(predictor_evaluation_workflow_dict: dict,
                        workflow: PredictorEvaluationWorkflow):
    session = FakeSession()
    session.set_response(predictor_evaluation_workflow_dict)
    collection = PredictorEvaluationWorkflowCollection(
        project_id=uuid.uuid4(),
        session=session
    )
    default_workflow = collection.create_default(predictor_id=uuid.uuid4())
    assert default_workflow.dump() == workflow.dump()


def test_fetch_status(session, workflow, predictor_evaluation_workflow_dict):
    with pytest.raises(RuntimeError):
        PredictorEvaluationWorkflow(name="foo", evaluators=[]).succeeded()
    session.set_response(predictor_evaluation_workflow_dict)
    assert not workflow.succeeded()
