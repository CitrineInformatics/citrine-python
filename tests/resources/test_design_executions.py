import pytest
import uuid

from citrine.informatics.executions.design_execution import DesignExecution
from citrine.resources.design_execution import DesignExecutionCollection
from tests.utils.factories import MLIScoreFactory
from tests.utils.session import FakeSession, FakeCall


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def collection(session) -> DesignExecutionCollection:
    return DesignExecutionCollection(
        project_id=uuid.uuid4(),
        workflow_id=uuid.uuid4(),
        session=session,
    )


@pytest.fixture
def workflow_execution(collection: DesignExecutionCollection, design_execution_dict) -> DesignExecution:
    return collection.build(design_execution_dict)


def test_basic_methods(workflow_execution, collection):
    assert "DesignExecution" in str(workflow_execution)

    with pytest.raises(NotImplementedError):
        collection.register(workflow_execution)

    with pytest.raises(NotImplementedError):
        collection.update(workflow_execution)

    with pytest.raises(NotImplementedError):
        collection.archive(workflow_execution)

    with pytest.raises(NotImplementedError):
        collection.restore(workflow_execution)


def test_build_new_execution(collection, design_execution_dict):
    # Given
    workflow_execution_id = uuid.uuid4()
    build_data = design_execution_dict.copy()
    build_data["id"] = str(workflow_execution_id)
    build_data["workflow_id"] = str(collection.workflow_id)

    # When
    execution: DesignExecution = collection.build(build_data)

    # Then
    assert execution.uid == workflow_execution_id
    assert execution.project_id == collection.project_id
    assert execution.workflow_id == collection.workflow_id
    assert execution._session == collection.session
    assert execution.in_progress() and not execution.succeeded() and not execution.failed()


def test_trigger_workflow_execution(collection: DesignExecutionCollection, design_execution_dict, session):
    # Given
    session.set_response(design_execution_dict)
    score = MLIScoreFactory()

    # When
    actual_execution = collection.trigger(score)

    # Then
    assert str(actual_execution.uid) == design_execution_dict["id"]
    expected_path = '/projects/{}/design-workflows/{}/executions'.format(
        collection.project_id,
        collection.workflow_id,
    )
    assert session.last_call == FakeCall(
        method='POST',
        path=expected_path,
        json={'score': score.dump()}
    )


def test_workflow_execution_results(workflow_execution: DesignExecution, session, example_candidates):
    # Given
    session.set_response(example_candidates)

    # When
    list(workflow_execution.candidates(per_page=4))

    # Then
    expected_path = '/projects/{}/design-workflows/{}/executions/{}/candidates'.format(
        workflow_execution.project_id,
        workflow_execution.workflow_id,
        workflow_execution.uid,
    )
    assert session.last_call == FakeCall(method='GET', path=expected_path, params={"per_page": 4})


def test_list(collection: DesignExecutionCollection, session):
    session.set_response({"per_page": 4, "next": "", "response": []})
    lst = list(collection.list(per_page=4))
    assert len(lst) == 0

    expected_path = '/projects/{}/design-workflows/{}/executions'.format(collection.project_id, collection.workflow_id)
    assert session.last_call == FakeCall(
        method='GET',
        path=expected_path,
        params={"per_page": 4}
    )


def test_delete(collection):
    with pytest.raises(NotImplementedError):
        collection.delete(uuid.uuid4())


def test_experimental_deprecated(collection, design_execution_dict):
    # Given
    workflow_execution_id = uuid.uuid4()
    build_data = design_execution_dict.copy()
    build_data["id"] = str(workflow_execution_id)
    build_data["workflow_id"] = str(collection.workflow_id)
    
    # When
    execution = collection.build(build_data)

    # Then
    with pytest.deprecated_call():
        assert execution.experimental is False
    with pytest.deprecated_call():
        assert execution.experimental_reasons == []
