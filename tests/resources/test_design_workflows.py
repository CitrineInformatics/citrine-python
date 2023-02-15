import itertools
import random
import uuid

import pytest

from citrine.informatics.workflows import DesignWorkflow
from citrine.resources.design_workflow import DesignWorkflowCollection
from tests.utils.factories import BranchDataFactory
from tests.utils.session import FakeSession, FakeCall

PARTIAL_DW_ARGS = (("predictor_id", uuid.uuid4), ("design_space_id", uuid.uuid4))
OPTIONAL_ARGS = PARTIAL_DW_ARGS + (("predictor_version", lambda: random.randint(1, 10)),)


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
    workflow.predictor_id = None
    workflow.predictor_version = None
    workflow.design_space_id = None
    return workflow


def all_combination_lengths(vals, maxlen=None):
    maxlen = maxlen or len(vals)
    return [args for k in range(0, maxlen + 1) for args in itertools.combinations(vals, k)]

def workflow_path(collection, workflow=None):
    path = f'/projects/{collection.project_id}/design-workflows'
    if workflow:
        path = f'{path}/{workflow.uid}'
    return path


def assert_workflow(actual, expected, *, include_branch=False):
    assert actual.name == expected.name
    assert actual.description == expected.description
    assert actual.archived == expected.archived
    assert actual.design_space_id == expected.design_space_id
    assert actual.predictor_id == expected.predictor_id
    assert actual.predictor_version == expected.predictor_version
    assert actual.project_id == expected.project_id
    if include_branch:
        assert actual.branch_id == expected.branch_id


def test_basic_methods(workflow, collection, design_workflow_dict):
    assert 'DesignWorkflow' in str(workflow)
    assert workflow.design_executions.project_id == workflow.project_id


@pytest.mark.parametrize("optional_args", all_combination_lengths(OPTIONAL_ARGS))
def test_register(session, workflow_minimal, collection, optional_args):
    workflow = workflow_minimal

    # Set a random value for all optional args selected for this run.
    for name, factory in optional_args:
        setattr(workflow, name, factory())

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


def test_deprecated_register_without_branch(session, workflow, collection_without_branch):
    # Given
    new_branch_id = uuid.uuid4()
    branch_response = BranchDataFactory(id=str(new_branch_id))
    branch_response["data"]["name"] = workflow.name
    post_dict = {**workflow.dump(), 'branch_id': str(new_branch_id)}
    session.set_responses(
        branch_response,
        {**post_dict, 'status_description': 'status'})

    # When
    # Future design workflow creation will require a branch.
    with pytest.deprecated_call():
        new_workflow = collection_without_branch.register(workflow)

    # Then
    assert session.num_calls == 2
    expected_call_create_branch = FakeCall(
        method='POST',
        path=f'/projects/{collection_without_branch.project_id}/branches',
        json={"name": workflow.name})
    expected_call_create_workflow = FakeCall(
        method='POST',
        path=workflow_path(collection_without_branch),
        json=post_dict,
        version="v2")
    assert session.calls == [expected_call_create_branch, expected_call_create_workflow]
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


def test_deprecated_register_only_model_has_branch(session, workflow, collection_without_branch):
    ### This situation should be handled the same way as when neither has a branch ID

    # Given
    new_branch_id = uuid.uuid4()
    old_branch_id = uuid.uuid4()
    
    workflow.branch_id = old_branch_id
    branch_response = BranchDataFactory(id=str(new_branch_id))
    branch_response["data"]["name"] = workflow.name
    post_dict = {**workflow.dump(), 'branch_id': str(new_branch_id)}
    session.set_responses(
        branch_response,
        {**post_dict, 'status_description': 'status'})


    # When
    # Future design workflow creation will require a branch ID.
    with pytest.deprecated_call():
        new_workflow = collection_without_branch.register(workflow)

    # Then
    assert session.num_calls == 2
    expected_call_create_branch = FakeCall(
        method='POST',
        path=f'/projects/{collection_without_branch.project_id}/branches',
        json={"name": workflow.name})
    expected_call_create_workflow = FakeCall(
        method='POST',
        path=workflow_path(collection_without_branch),
        json=post_dict,
        version="v2")
    assert session.calls == [expected_call_create_branch, expected_call_create_workflow]
    assert collection_without_branch.branch_id is None
    assert workflow.branch_id == old_branch_id
    assert new_workflow.branch_id == new_branch_id
    assert_workflow(new_workflow, workflow)


@pytest.mark.parametrize("partial_args",
                         all_combination_lengths(PARTIAL_DW_ARGS, len(PARTIAL_DW_ARGS) - 1))
def test_register_partial_workflow_without_branch(session, workflow_minimal, collection_without_branch, partial_args):
    workflow = workflow_minimal

    # Set a random value for all optional args selected for this run.
    for name, factory in partial_args:
        setattr(workflow, name, factory())

    new_branch_id = uuid.uuid4()
    branch_response = BranchDataFactory(id=str(new_branch_id))
    branch_response["data"]["name"] = workflow.name
    post_dict = {**workflow.dump(), 'branch_id': str(new_branch_id)}
    session.set_responses(
        branch_response,
        {**post_dict, 'status_description': 'status'})

    with pytest.deprecated_call():
        collection_without_branch.register(workflow)
    
    assert session.calls == [
        FakeCall(
            method='POST',
            path=f'/projects/{collection_without_branch.project_id}/branches',
            json={"name": workflow.name}),
        FakeCall(
            method='POST',
            path=workflow_path(collection_without_branch),
            json=post_dict,
            version="v2")
    ]


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
        predictor_id=design_workflow_dict["predictor_id"],
        predictor_version=design_workflow_dict["predictor_version"],
        design_space_id=design_workflow_dict["design_space_id"]
    )

    with pytest.raises(AttributeError):
        workflow.design_executions


def test_update(session, workflow, collection_without_branch):
    # Given
    workflow.branch_id = uuid.uuid4()

    post_dict = workflow.dump()
    session.set_responses(
        {"per_page": 1, "next": "", "response": []},
        {**post_dict, 'status_description': 'status'})

    # When
    new_workflow = collection_without_branch.update(workflow)

    # Then
    assert session.num_calls == 2
    expected_call = FakeCall(
        method='PUT',
        path=workflow_path(collection_without_branch, workflow),
        json=post_dict)
    assert session.last_call == expected_call
    assert_workflow(new_workflow, workflow)


def test_update_warning(session, workflow, collection_without_branch, design_execution_dict):
    # Given
    workflow.branch_id = uuid.uuid4()
    post_dict = workflow.dump()
    session.set_responses(
        {"per_page": 1, "next": "", "response": [design_execution_dict]},
        {**post_dict, 'status_description': 'status'})

    # When
    with pytest.deprecated_call():
        new_workflow = collection_without_branch.update(workflow)

    # Then
    assert session.num_calls == 2
    expected_call = FakeCall(
        method='PUT',
        path=workflow_path(collection_without_branch, workflow),
        json=post_dict)
    assert session.last_call == expected_call
    assert_workflow(new_workflow, workflow)


def test_update_with_matching_branch_ids(session, workflow, collection):
    # Given
    workflow.branch_id = collection.branch_id

    post_dict = workflow.dump()
    session.set_responses(
        {"per_page": 1, "next": "", "response": []},
        {**post_dict, 'status_description': 'status'})

    # When
    new_workflow = collection.update(workflow)

    # Then
    assert session.num_calls == 2
    expected_call = FakeCall(
        method='PUT',
        path=workflow_path(collection, workflow),
        json=post_dict)
    assert session.last_call == expected_call
    assert_workflow(new_workflow, workflow)


def test_update_with_mismatched_branch_ids(session, workflow, collection):
    # Given
    workflow.branch_id = uuid.uuid4()

    # Then/When
    with pytest.raises(ValueError):
        collection.update(workflow)


def test_update_model_missing_branch_id(session, workflow, collection_without_branch):
    # Given

    # Then/When
    with pytest.raises(ValueError):
        collection_without_branch.update(workflow)
