import uuid

import pytest

from citrine.informatics.modules import ModuleRef
from citrine.informatics.design_candidate import DesignCandidate
from citrine.resources.design_execution import DesignExecutionCollection, DesignExecution
from tests.utils.session import FakeSession, FakeCall
from tests.utils.factories import MLIScoreFactory


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


def test_build_new_execution(collection, design_execution_dict):
    # Given
    workflow_execution_id = uuid.uuid4()
    build_data = design_execution_dict.copy()
    build_data["id"] = str(workflow_execution_id)
    build_data["workflow_id"] = str(collection.workflow_id)

    # When
    execution = collection.build(build_data)

    # Then
    assert execution.uid == workflow_execution_id
    assert execution.project_id == collection.project_id
    assert execution.workflow_id == collection.workflow_id
    assert execution.session == collection.session


def test_trigger_workflow_execution(collection: DesignExecutionCollection, design_execution_dict, session):
    # Given
    predictor_id = uuid.uuid4()
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


def test_list(collection: DesignExecutionCollection, session):
    session.set_response({"page": 2, "per_page": 4, "next": "foo", "response": []})
    lst = list(collection.list(2, 4))
    assert len(lst) == 0

    expected_path = '/projects/{}/design-workflows/{}/executions'.format(collection.project_id, collection.workflow_id)
    assert session.last_call == FakeCall(
        method='GET',
        path=expected_path,
        params={"page": 2, "per_page": 4}
    )


def test_archive(workflow_execution, collection):
    collection.archive(workflow_execution.uid)
    expected_path = '/projects/{}/design-workflows/{}/executions/{}/archive'.format(collection.project_id, collection.workflow_id, workflow_execution.uid)
    assert collection.session.last_call == FakeCall(method='PUT', path=expected_path, json={})


def test_restore(workflow_execution, collection):
    collection.restore(workflow_execution.uid)
    expected_path = '/projects/{}/design-workflows/{}/executions/{}/restore'.format(collection.project_id, collection.workflow_id, workflow_execution.uid)
    assert collection.session.last_call == FakeCall(method='PUT', path=expected_path, json={})


def test_delete(collection):
    with pytest.raises(NotImplementedError):
        collection.delete(uuid.uuid4())
