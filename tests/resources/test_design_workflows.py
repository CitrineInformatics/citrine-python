import uuid

import pytest

from citrine.informatics.workflows import NewDesignWorkflow
from citrine.resources.design_workflow import DesignWorkflowCollection
from tests.utils.session import FakeSession, FakeCall


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def collection(session) -> DesignWorkflowCollection:
    return DesignWorkflowCollection(
        project_id=uuid.uuid4(),
        session=session,
    )


@pytest.fixture
def workflow(collection: DesignWorkflowCollection, design_workflow_dict) -> NewDesignWorkflow:
    return collection.build(design_workflow_dict)


def test_basic_methods(workflow, collection):
    assert "NewDesignWorkflow" in str(workflow)
    # assert workflow.evaluators[0].name == "Example evaluator"


def test_archive(workflow, collection):
    collection.archive(workflow.uid)
    expected_path = '/projects/{}/design-workflows/{}/archive'.format(collection.project_id, workflow.uid)
    assert collection.session.last_call == FakeCall(method='PUT', path=expected_path, json={})


def test_restore(workflow, collection):
    collection.restore(workflow.uid)
    expected_path = '/projects/{}/design-workflows/{}/restore'.format(collection.project_id, workflow.uid)
    assert collection.session.last_call == FakeCall(method='PUT', path=expected_path, json={})


def test_delete(collection):
    with pytest.raises(NotImplementedError):
        collection.delete(uuid.uuid4())
