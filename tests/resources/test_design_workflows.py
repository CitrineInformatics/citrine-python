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
def branch_data():
    return BranchDataFactory()


@pytest.fixture
def collection(branch_data, collection_without_branch) -> DesignWorkflowCollection:
    return DesignWorkflowCollection(
        project_id=collection_without_branch.project_id,
        session=collection_without_branch.session,
        branch_root_id=uuid.UUID(branch_data['metadata']['root_id']),
        branch_version=branch_data['metadata']['version'],

    )


@pytest.fixture
def workflow(collection, branch_data, design_workflow_dict) -> DesignWorkflow:
    design_workflow_dict["branch_id"] = branch_data["id"]

    collection.session.set_response(branch_data)
    workflow = collection.build(design_workflow_dict)
    collection.session.calls.clear()

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

def branches_path(collection, branch_id=None):
    path = f'/projects/{collection.project_id}/branches'
    if branch_id:
        path = f'{path}/{branch_id}'
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
        assert actual.branch_root_id == expected.branch_root_id
        assert actual.branch_version == expected.branch_version


def test_basic_methods(workflow, collection, design_workflow_dict):
    assert 'DesignWorkflow' in str(workflow)
    assert workflow.design_executions.project_id == workflow.project_id


@pytest.mark.parametrize("optional_args", all_combination_lengths(OPTIONAL_ARGS))
def test_register(session, branch_data, workflow_minimal, collection, optional_args):
    workflow = workflow_minimal
    branch_id = branch_data['id']
    branch_data_get_resp = {"response": [branch_data]}
    branch_data_get_params = {
        'page': 1, 'per_page': 1, 'root': str(collection.branch_root_id), 'version': collection.branch_version
    }

    # Set a random value for all optional args selected for this run.
    for name, factory in optional_args:
        setattr(workflow, name, factory())

    # Given
    post_dict = {**workflow.dump(), "branch_id": str(branch_id)}
    session.set_responses(branch_data_get_resp, {**post_dict, 'status_description': 'status'}, branch_data)

    # When
    new_workflow = collection.register(workflow)

    # Then
    assert session.calls == [
        FakeCall(method='GET', path=branches_path(collection), params=branch_data_get_params),
        FakeCall(method='POST', path=workflow_path(collection), json=post_dict),
        FakeCall(method='GET', path=branches_path(collection, branch_id)),
    ]

    assert new_workflow.branch_root_id == collection.branch_root_id
    assert new_workflow.branch_version == collection.branch_version
    assert_workflow(new_workflow, workflow)


def test_register_conflicting_branches(session, branch_data, workflow, collection):
    # Given
    old_branch_root_id = uuid.uuid4()
    workflow.branch_root_id = old_branch_root_id
    assert workflow.branch_root_id != collection.branch_root_id

    branch_data_get_resp = {"response": [branch_data]}
    branch_data_get_params = {
        'page': 1, 'per_page': 1, 'root': str(collection.branch_root_id), 'version': collection.branch_version
    }
    post_dict = {**workflow.dump(), "branch_id": str(branch_data["id"])}
    session.set_responses(branch_data_get_resp, {**post_dict, 'status_description': 'status'}, branch_data)

    # When
    new_workflow = collection.register(workflow)

    # Then
    assert session.calls == [
        FakeCall(method='GET', path=branches_path(collection), params=branch_data_get_params),
        FakeCall(method='POST', path=workflow_path(collection), json=post_dict),
        FakeCall(method='GET', path=branches_path(collection, branch_data["id"])),
    ]

    assert workflow.branch_root_id == old_branch_root_id
    assert new_workflow.branch_root_id == collection.branch_root_id
    assert_workflow(new_workflow, workflow)


def test_register_partial_workflow_without_branch(session, workflow_minimal, collection_without_branch):
    workflow = workflow_minimal
    with pytest.raises(RuntimeError):
        collection_without_branch.register(workflow)


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


def test_list_archived(branch_data, workflow, collection: DesignWorkflowCollection):
    branch_data_get_resp = {"response": [branch_data]}
    branch_id = uuid.UUID(branch_data['id'])

    collection.session.set_responses(branch_data_get_resp, {"response": []})

    lst = list(collection.list_archived(per_page=10))
    assert len(lst) == 0

    expected_path = '/projects/{}/design-workflows'.format(collection.project_id)
    assert collection.session.last_call == FakeCall(
        method='GET',
        path=expected_path,
        params={'page': 1, 'per_page': 10, 'filter': "archived eq 'true'", 'branch': branch_id},
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


def test_update(session, branch_data, workflow, collection_without_branch):
    # Given
    branch_data_get_resp = {"response": [branch_data]}
    branch_data_get_params = {
        'page': 1, 'per_page': 1, 'root': str(workflow.branch_root_id), 'version': workflow.branch_version
    }

    post_dict = workflow.dump()
    session.set_responses(
        branch_data_get_resp,
        {"per_page": 1, "next": "", "response": []},
        {**post_dict, 'status_description': 'status'},
        branch_data
    )

    # When
    new_workflow = collection_without_branch.update(workflow)

    # Then
    executions_path = f'/projects/{collection_without_branch.project_id}/design-workflows/{workflow.uid}/executions'
    assert session.calls == [
        FakeCall(method='GET', path=branches_path(collection_without_branch), params=branch_data_get_params),
        FakeCall(method='GET', path=executions_path, params={'page': 1, 'per_page': 100}),
        FakeCall(method='PUT', path=workflow_path(collection_without_branch, workflow), json=post_dict),
        FakeCall(method='GET', path=branches_path(collection_without_branch, branch_data["id"])),
    ]
    assert_workflow(new_workflow, workflow)


def test_update_failure_with_existing_execution(session, branch_data, workflow, collection_without_branch, design_execution_dict):
    branch_data_get_resp = {"response": [branch_data]}
    workflow.branch_root_id = uuid.uuid4()
    post_dict = workflow.dump()
    session.set_responses(
        branch_data_get_resp,
        {"per_page": 1, "next": "", "response": [design_execution_dict]},
        {**post_dict, 'status_description': 'status'})

    with pytest.raises(RuntimeError):
        collection_without_branch.update(workflow)


def test_update_with_mismatched_branch_ids(session, workflow, collection):
    # Given
    workflow.branch_root_id = uuid.uuid4()

    # Then/When
    with pytest.raises(ValueError):
        collection.update(workflow)


def test_update_model_missing_branch_root_id(session, workflow, collection_without_branch):
    # Given
    workflow.branch_root_id = None

    # Then/When
    with pytest.raises(ValueError):
        collection_without_branch.update(workflow)


def test_update_model_missing_branch_version(session, workflow, collection_without_branch):
    # Given
    workflow.branch_version = None

    # Then/When
    with pytest.raises(ValueError):
        collection_without_branch.update(workflow)


def test_update_branch_not_found(collection, workflow):
    collection.session.set_responses({"response": []})

    # When
    with pytest.raises(ValueError):
        collection.update(workflow)


def test_update_branch_id_deprecated(session, branch_data, workflow, collection_without_branch):
    # Given
    workflow.branch_root_id = None
    workflow.branch_version = None
    with pytest.deprecated_call():
        workflow.branch_id = branch_data['id']

    post_dict = workflow.dump()
    session.set_responses(
        {"per_page": 1, "next": "", "response": []},
        {**post_dict, 'status_description': 'status'},
        branch_data
    )

    # When
    new_workflow = collection_without_branch.update(workflow)

    # Then
    executions_path = f'/projects/{collection_without_branch.project_id}/design-workflows/{workflow.uid}/executions'
    assert session.calls == [
        FakeCall(method='GET', path=executions_path, params={'page': 1, 'per_page': 100}),
        FakeCall(method='PUT', path=workflow_path(collection_without_branch, workflow), json=post_dict),
        FakeCall(method='GET', path=branches_path(collection_without_branch, branch_data["id"])),
    ]
    assert_workflow(new_workflow, workflow)
    with pytest.deprecated_call():
        assert new_workflow.branch_id == workflow.branch_id
