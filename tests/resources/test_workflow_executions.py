import uuid

import pytest

from citrine.resources.workflow_executions import WorkflowExecutionCollection, WorkflowExecution, \
    WorkflowExecutionStatus
from tests.utils.factories import MLIScoreFactory
from tests.utils.session import FakeSession, FakeCall


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def collection(session) -> WorkflowExecutionCollection:
    return WorkflowExecutionCollection(
        project_id=uuid.uuid4(),
        workflow_id=uuid.uuid4(),
        session=session,
    )


@pytest.fixture
def workflow_execution(session) -> WorkflowExecution:
    return WorkflowExecution(
        uid=str(uuid.uuid4()),
        project_id=str(uuid.uuid4()),
        workflow_id=str(uuid.uuid4()),
        session=session,
        version_number=1
    )


def test_build_new_execution(collection):
    # Given
    workflow_execution_id = uuid.uuid4()
    build_data = {'id': str(workflow_execution_id), 'version_number': 1}

    # When
    execution = collection.build(build_data)

    # Then
    assert execution.uid == workflow_execution_id
    assert execution.project_id == collection.project_id
    assert execution.workflow_id == collection.workflow_id
    assert execution.session == collection.session


def test_workflow_execution_status(workflow_execution, session):
    # Given
    session.set_response({'status': 'Succeeded'})

    # When
    status = workflow_execution.status()

    # Then
    assert status.status == 'Succeeded'
    expected_path = '/projects/{}/workflows/{}/executions/{}/status'.format(
        workflow_execution.project_id,
        workflow_execution.workflow_id,
        workflow_execution.uid,
    )
    assert session.last_call == FakeCall(method='GET', path=expected_path)


def test_workflow_execution_results(workflow_execution, session):
    # Given
    session.set_response({'foo': 'GREAT RESULTS'})

    # When
    results = workflow_execution.results()

    # Then
    assert results == {'foo': 'GREAT RESULTS'}
    expected_path = '/projects/{}/workflows/{}/executions/{}/results'.format(
        workflow_execution.project_id,
        workflow_execution.workflow_id,
        workflow_execution.uid,
    )
    assert session.last_call == FakeCall(method='GET', path=expected_path)

def test_workflow_execution_candidates(workflow_execution, example_candidates, session):
    # Given
    session.set_response(example_candidates)

    # When
    results = list(workflow_execution.candidates(page=2, per_page=4))

    # Then
    expected_path = '/projects/{}/design-workflows/{}/executions/{}/candidates'.format(
        workflow_execution.project_id,
        workflow_execution.workflow_id,
        workflow_execution.uid,
    )
    assert session.last_call == FakeCall(method='GET', path=expected_path, params={"page": 2, "per_page": 4})


def test_trigger_workflow_execution(collection: WorkflowExecutionCollection, workflow_execution, session):
    # Given
    session.set_response(workflow_execution.dump())

    # When
    score = MLIScoreFactory()
    # triggering legacy Workflows has been removed
    with pytest.raises(NotImplementedError):
        actual_execution = collection.trigger(score)


def test_workflow_success_status():
    status = WorkflowExecutionStatus('Succeeded', None)

    assert status.succeeded
    assert not status.in_progress
    assert not status.failed
    assert not status.timed_out


def test_workflow_in_progress_status():
    status = WorkflowExecutionStatus('InProgress', None)

    assert not status.succeeded
    assert not status.timed_out
    assert status.in_progress
    assert not status.failed


def test_workflow_failed_status():
    status = WorkflowExecutionStatus('Failed', None)

    assert not status.succeeded
    assert not status.in_progress
    assert not status.timed_out
    assert status.failed


def test_workflow_timedout_status():
    status = WorkflowExecutionStatus('TimedOut', None)

    assert not status.succeeded
    assert not status.in_progress
    assert not status.failed
    assert status.timed_out
