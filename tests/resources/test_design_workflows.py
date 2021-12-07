import uuid
from itertools import combinations

import pytest

from citrine.informatics.workflows import DesignWorkflow
from citrine.resources.design_workflow import DesignWorkflowCollection
from tests.utils.session import FakeSession, FakeCall


OPTIONAL_ARGS = ("processor_id", "predictor_id", "design_space_id")


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def collection_without_branch(session) -> DesignWorkflowCollection:
    return DesignWorkflowCollection(
        project_id=uuid.uuid4(),
        session=session,
    )


@pytest.fixture
def collection(collection_without_branch) -> DesignWorkflowCollection:
    return DesignWorkflowCollection(
        project_id=collection_without_branch.project_id,
        session=collection_without_branch.session,
        branch_id=uuid.uuid4()
    )


@pytest.fixture
def workflow(collection, design_workflow_dict) -> DesignWorkflow:
    workflow = collection.build(design_workflow_dict)
    workflow.uid = uuid.uuid4()
    return workflow


@pytest.fixture
def workflow_minimal(collection, workflow) -> DesignWorkflow:
    workflow.processor_id = None
    workflow.predictor_id = None
    workflow.design_space_id = None
    return workflow


def workflow_path(collection):
    return f'/projects/{collection.project_id}/design-workflows'


def assert_workflow(actual, expected, *, include_branch=False):
    assert actual.name == expected.name
    assert actual.description == expected.description
    assert actual.archived == expected.archived
    assert actual.design_space_id == expected.design_space_id
    assert actual.processor_id == expected.processor_id
    assert actual.predictor_id == expected.predictor_id
    assert actual.project_id == expected.project_id
    if include_branch:
        assert actual.branch_id == expected.branch_id


def test_basic_methods(workflow, collection, design_workflow_dict):
    assert 'DesignWorkflow' in str(workflow)
    assert workflow.design_executions.project_id == workflow.project_id


@pytest.mark.parametrize("optional_args",
        [args for k in range(0, len(OPTIONAL_ARGS) + 1) for args in combinations(OPTIONAL_ARGS, k)])
def test_register(session, workflow_minimal, collection, optional_args):
    workflow = workflow_minimal

    # Set a random UUID for all optional args selected for this run.
    for arg in optional_args:
        setattr(workflow, arg, uuid.uuid4())

    # Given
    post_dict = {**workflow.dump(), "branch_id": str(collection.branch_id)}
    session.set_response({**post_dict, 'status_description': 'status'})

    # When
    new_workflow = collection.register(workflow)

    # Then
    assert session.num_calls == 1
    expected_call = FakeCall(
        method='POST',
        path=workflow_path(collection),
        json=post_dict)
    assert session.last_call == expected_call
    assert new_workflow.branch_id == collection.branch_id
    assert_workflow(new_workflow, workflow)


def test_register_without_branch(session, workflow, collection_without_branch):
    # Given
    new_branch_id = uuid.uuid4()
    post_dict = workflow.dump()
    session.set_responses(
        {**post_dict, 'id': str(workflow.uid), 'status_description': 'status'},
        {**post_dict, 'branch_id': str(new_branch_id), 'status_description': 'status'})

    # When
    new_workflow = collection_without_branch.register(workflow)

    # Then
    assert session.num_calls == 2
    expected_call_create = FakeCall(
        method='POST',
        path=workflow_path(collection_without_branch),
        json=post_dict)
    expected_call_get_branch = FakeCall(
        method='GET',
        path=f'{workflow_path(collection_without_branch)}/{workflow.uid}')
    assert session.calls == [expected_call_create, expected_call_get_branch]
    assert collection_without_branch.branch_id is None
    assert workflow.branch_id is None
    assert new_workflow.branch_id == new_branch_id
    assert_workflow(new_workflow, workflow)


def test_register_conflicting_branches(session, workflow, collection):
    # Given
    old_branch_id = uuid.uuid4()
    workflow.branch_id = old_branch_id
    assert workflow.branch_id != collection.branch_id

    post_dict = {**workflow.dump(), "branch_id": str(collection.branch_id)}
    session.set_response({**post_dict, 'status_description': 'status'})

    # When
    new_workflow = collection.register(workflow)

    # Then
    assert session.num_calls == 1
    expected_call = FakeCall(
        method='POST',
        path=workflow_path(collection),
        json=post_dict)
    assert session.last_call == expected_call
    assert workflow.branch_id == old_branch_id
    assert new_workflow.branch_id == collection.branch_id
    assert_workflow(new_workflow, workflow)


def test_register_only_model_has_branch(session, workflow, collection_without_branch):
    ### Should match the result when neither has a branch ID

    # Given
    new_branch_id = uuid.uuid4()
    old_branch_id = uuid.uuid4()
    
    workflow.branch_id = old_branch_id
    post_dict = workflow.dump()
    session.set_responses(
        {**post_dict, 'id': str(workflow.uid), 'status_description': 'status'},
        {**post_dict, 'branch_id': str(new_branch_id), 'status_description': 'status'})

    # When
    new_workflow = collection_without_branch.register(workflow)

    # Then
    assert session.num_calls == 2
    expected_call_create = FakeCall(
        method='POST',
        path=workflow_path(collection_without_branch),
        json=post_dict)
    expected_call_get_branch = FakeCall(
        method='GET',
        path=f'{workflow_path(collection_without_branch)}/{workflow.uid}')
    assert session.calls == [expected_call_create, expected_call_get_branch]
    assert collection_without_branch.branch_id is None
    assert workflow.branch_id == old_branch_id
    assert new_workflow.branch_id == new_branch_id
    assert_workflow(new_workflow, workflow)


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


def test_list_archived(workflow, collection: DesignWorkflowCollection):
    collection.session.set_response({"response": []})
    lst = list(collection.list_archived(per_page=10))
    assert len(lst) == 0

    expected_path = '/projects/{}/design-workflows'.format(collection.project_id)
    assert collection.session.last_call == FakeCall(
        method='GET',
        path=expected_path,
        params={'per_page': 10, 'filter': "archived eq 'true'", 'branch': collection.branch_id},
        json=None
    )


def test_missing_project(design_workflow_dict):
    """Make sure we get an attribute error if there is no project id."""

    workflow = DesignWorkflow(
        name=design_workflow_dict["name"],
        processor_id=design_workflow_dict["processor_id"],
        predictor_id=design_workflow_dict["predictor_id"],
        design_space_id=design_workflow_dict["design_space_id"]
    )

    with pytest.raises(AttributeError):
        workflow.design_executions
