import random
import uuid

import pytest

from citrine._rest.resource import PredictorRef
from citrine.informatics.executions.predictor_evaluation_execution import PredictorEvaluationExecution
from citrine.informatics.predictor_evaluation_result import PredictorEvaluationResult
from citrine.resources.predictor_evaluation_execution import PredictorEvaluationExecutionCollection
from tests.utils.session import FakeSession, FakeCall


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def collection(session) -> PredictorEvaluationExecutionCollection:
    return PredictorEvaluationExecutionCollection(
        project_id=uuid.uuid4(),
        workflow_id=uuid.uuid4(),
        session=session,
    )


@pytest.fixture
def workflow_execution(collection: PredictorEvaluationExecutionCollection, predictor_evaluation_execution_dict) -> PredictorEvaluationExecution:
    return collection.build(predictor_evaluation_execution_dict)


def test_basic_methods(workflow_execution, collection):
    assert "PredictorEvaluationExecution" in str(workflow_execution)

    with pytest.raises(TypeError):
        workflow_execution[12]

    assert "Example evaluator" in list(iter(workflow_execution))

    with pytest.raises(NotImplementedError):
        collection.register(workflow_execution)

    with pytest.raises(NotImplementedError):
        collection.update(workflow_execution)


def test_build_new_execution(collection, predictor_evaluation_execution_dict):
    # Given
    workflow_execution_id = uuid.uuid4()
    build_data = predictor_evaluation_execution_dict.copy()
    build_data["id"] = str(workflow_execution_id)
    build_data["workflow_id"] = str(collection.workflow_id)

    # When
    execution: PredictorEvaluationExecution = collection.build(build_data)

    # Then
    assert execution.uid == workflow_execution_id
    assert execution.project_id == collection.project_id
    assert execution.workflow_id == collection.workflow_id
    assert execution._session == collection.session
    assert execution.in_progress() and not execution.succeeded() and not execution.failed()
    assert execution.status_detail
    with pytest.deprecated_call():
        assert execution.status_info == [detail.msg for detail in execution.status_detail]


def test_workflow_execution_results(workflow_execution: PredictorEvaluationExecution, session,
                                    example_cv_result_dict):
    # Given
    session.set_response(example_cv_result_dict)

    # When
    results = workflow_execution["Example Evaluator"]

    # Then
    assert results.evaluator == PredictorEvaluationResult.build(example_cv_result_dict).evaluator
    expected_path = '/projects/{}/predictor-evaluation-executions/{}/results'.format(
        workflow_execution.project_id,
        workflow_execution.uid,
    )
    assert session.last_call == FakeCall(method='GET', path=expected_path, params={"evaluator_name": "Example Evaluator"})


def test_trigger_workflow_execution(collection: PredictorEvaluationExecutionCollection, predictor_evaluation_execution_dict, session):
    # Given
    predictor_id = uuid.uuid4()
    random_state = 9325
    session.set_response(predictor_evaluation_execution_dict)

    # When
    actual_execution = collection.trigger(predictor_id, random_state=random_state)

    # Then
    assert str(actual_execution.uid) == predictor_evaluation_execution_dict["id"]
    expected_path = '/projects/{}/predictor-evaluation-workflows/{}/executions'.format(
        collection.project_id,
        collection.workflow_id,
    )
    assert session.last_call == FakeCall(
        method='POST',
        path=expected_path,
        json=PredictorRef(predictor_id).dump(),
        params={"random_state": random_state}
    )


def test_trigger_workflow_execution_with_version(collection: PredictorEvaluationExecutionCollection, predictor_evaluation_execution_dict, session):
    # Given
    predictor_id = uuid.uuid4()
    predictor_version = random.randint(1, 10)
    session.set_response(predictor_evaluation_execution_dict)

    # When
    actual_execution = collection.trigger(predictor_id, predictor_version=predictor_version)

    # Then
    assert str(actual_execution.uid) == predictor_evaluation_execution_dict["id"]
    expected_path = '/projects/{}/predictor-evaluation-workflows/{}/executions'.format(
        collection.project_id,
        collection.workflow_id,
    )
    assert session.last_call == FakeCall(
        method='POST',
        path=expected_path,
        json=PredictorRef(predictor_id, predictor_version).dump()
    )


@pytest.mark.parametrize("predictor_version", (2, "1", "latest", None))
def test_list(collection: PredictorEvaluationExecutionCollection, session, predictor_version):
    session.set_response({"page": 1, "per_page": 4, "next": "", "response": []})
    predictor_id = uuid.uuid4()
    lst = list(collection.list(per_page=4, predictor_id=predictor_id, predictor_version=predictor_version))
    assert not lst

    expected_path = '/projects/{}/predictor-evaluation-executions'.format(collection.project_id)
    expected_payload = {"per_page": 4, "predictor_id": str(predictor_id), "workflow_id": str(collection.workflow_id), 'page': 1}
    if predictor_version is not None:
        expected_payload["predictor_version"] = predictor_version
    assert session.last_call == FakeCall(method='GET', path=expected_path, params=expected_payload)


def test_archive(workflow_execution, collection):
    collection.archive(workflow_execution.uid)
    expected_path = '/projects/{}/predictor-evaluation-executions/archive'.format(collection.project_id)
    assert collection.session.last_call == FakeCall(method='PUT', path=expected_path, json={"module_uid": str(workflow_execution.uid)})


def test_restore(workflow_execution, collection):
    collection.restore(workflow_execution.uid)
    expected_path = '/projects/{}/predictor-evaluation-executions/restore'.format(collection.project_id)
    assert collection.session.last_call == FakeCall(method='PUT', path=expected_path, json={"module_uid": str(workflow_execution.uid)})


def test_delete(collection):
    with pytest.raises(NotImplementedError):
        collection.delete(uuid.uuid4())
