import itertools
import random
import uuid

import pytest

from citrine.informatics.workflows import DesignWorkflow
from citrine.resources.design_workflow import DesignWorkflowCollection
from tests.utils.factories import (
    BranchDataFactory,
    DesignWorkflowDataFactory,
    TableDataSourceFactory,
)
from tests.utils.session import FakeSession, FakeCall

PARTIAL_DW_ARGS = (
    ("data_source_id", lambda: TableDataSourceFactory().to_data_source_id()),
    ("predictor_id", lambda: str(uuid.uuid4())),
    ("design_space_id", lambda: str(uuid.uuid4())),
)
OPTIONAL_ARGS = PARTIAL_DW_ARGS + (
    ("predictor_version", lambda: random.randint(1, 10)),
)


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
        branch_root_id=uuid.UUID(branch_data["metadata"]["root_id"]),
        branch_version=branch_data["metadata"]["version"],
    )


@pytest.fixture
def workflow(collection, branch_data) -> DesignWorkflow:
    workflow_data = DesignWorkflowDataFactory(branch=branch_data, register=True)
    return collection.build(workflow_data)


def all_combination_lengths(vals, maxlen=None):
    maxlen = maxlen or len(vals)
    return [
        args for k in range(0, maxlen + 1) for args in itertools.combinations(vals, k)
    ]


def workflow_path(collection, workflow=None):
    path = f"/projects/{collection.project_id}/design-workflows"
    if workflow:
        path = f"{path}/{workflow.uid}"
    return path


def assert_workflow(actual, expected, *, include_branch=False):
    assert actual.name == expected.name
    assert actual.description == expected.description
    assert actual.archived == expected.archived
    assert actual.design_space_id == expected.design_space_id
    assert actual.predictor_id == expected.predictor_id
    assert actual.predictor_version == expected.predictor_version
    assert actual.data_source_id == expected.data_source_id
    assert actual.project_id == expected.project_id
    if include_branch:
        assert actual._branch_id == expected._branch_id
        assert actual.branch_root_id == expected.branch_root_id
        assert actual.branch_version == expected.branch_version


def test_basic_methods(workflow, collection):
    assert "DesignWorkflow" in str(workflow)
    assert workflow.design_executions.project_id == workflow.project_id


@pytest.mark.parametrize("optional_args", all_combination_lengths(OPTIONAL_ARGS))
def test_register(session, branch_data, collection, optional_args):
    kw_args = {argument: None for argument, factory in OPTIONAL_ARGS}
    kw_args.update({argument: factory() for argument, factory in optional_args})
    workflow_data = DesignWorkflowDataFactory(**kw_args, branch=branch_data)

    # Given
    post_dict = {k: v for k, v in workflow_data.items() if k != "status_description"}
    session.set_responses(workflow_data)

    # When
    old_workflow = collection.build(workflow_data)
    new_workflow = collection.register(old_workflow)

    # Then
    assert session.calls == [
        FakeCall(method="POST", path=workflow_path(collection), json=post_dict)
    ]

    assert new_workflow.branch_root_id == collection.branch_root_id
    assert new_workflow.branch_version == collection.branch_version
    assert_workflow(new_workflow, old_workflow)


def test_register_conflicting_branches(session, branch_data, workflow, collection):
    # Given
    old_branch_root_id = uuid.uuid4()
    workflow.branch_root_id = old_branch_root_id
    assert workflow.branch_root_id != collection.branch_root_id

    new_branch_root_id = str(branch_data["metadata"]["root_id"])
    new_branch_version = branch_data["metadata"]["version"]

    post_dict = {
        **workflow.dump(),
        "branch_root_id": new_branch_root_id,
        "branch_version": new_branch_version,
    }
    session.set_responses({**post_dict, "status_description": "status"})

    # When
    new_workflow = collection.register(workflow)

    # Then
    assert session.calls == [
        FakeCall(method="POST", path=workflow_path(collection), json=post_dict)
    ]

    assert workflow.branch_root_id == old_branch_root_id
    assert new_workflow.branch_root_id == collection.branch_root_id
    assert_workflow(new_workflow, workflow)


def test_register_partial_workflow_without_branch(session, collection_without_branch):
    workflow = DesignWorkflow.build(DesignWorkflowDataFactory())
    with pytest.raises(RuntimeError):
        collection_without_branch.register(workflow)


def test_archive(workflow, collection):
    collection.archive(workflow.uid)
    expected_path = "/projects/{}/design-workflows/{}/archive".format(
        collection.project_id, workflow.uid
    )
    assert collection.session.last_call == FakeCall(
        method="PUT", path=expected_path, json={}
    )


def test_restore(workflow, collection):
    collection.restore(workflow.uid)
    expected_path = "/projects/{}/design-workflows/{}/restore".format(
        collection.project_id, workflow.uid
    )
    assert collection.session.last_call == FakeCall(
        method="PUT", path=expected_path, json={}
    )


def test_delete(collection):
    with pytest.raises(NotImplementedError):
        collection.delete(uuid.uuid4())


def test_list_archived(branch_data, workflow, collection: DesignWorkflowCollection):
    branch_root_id = uuid.UUID(branch_data["metadata"]["root_id"])
    branch_version = branch_data["metadata"]["version"]

    collection.session.set_responses({"response": []})

    lst = list(collection.list_archived(per_page=10))
    assert len(lst) == 0

    expected_path = "/projects/{}/design-workflows".format(collection.project_id)
    assert collection.session.last_call == FakeCall(
        method="GET",
        path=expected_path,
        params={
            "page": 1,
            "per_page": 10,
            "filter": "archived eq 'true'",
            "branch_root_id": branch_root_id,
            "branch_version": branch_version,
        },
        json=None,
    )


def test_missing_project():
    """Make sure we get an attribute error if there is no project id."""

    workflow = DesignWorkflow.build(DesignWorkflowDataFactory())
    assert workflow.project_id is None  # Verify test assumption still holds

    with pytest.raises(AttributeError):
        workflow.design_executions


def test_update(session, branch_data, workflow, collection_without_branch):
    # Given
    post_dict = workflow.dump()
    session.set_responses(
        {"per_page": 1, "next": "", "response": []},
        {**post_dict, "status_description": "status"},
    )

    # When
    new_workflow = collection_without_branch.update(workflow)

    # Then
    executions_path = f"/projects/{collection_without_branch.project_id}/design-workflows/{workflow.uid}/executions"
    assert session.calls == [
        FakeCall(
            method="GET", path=executions_path, params={"page": 1, "per_page": 100}
        ),
        FakeCall(
            method="PUT",
            path=workflow_path(collection_without_branch, workflow),
            json=post_dict,
        ),
    ]
    assert_workflow(new_workflow, workflow)


def test_update_failure_with_existing_execution(
    session, branch_data, workflow, collection_without_branch, design_execution_dict
):
    workflow.branch_root_id = uuid.uuid4()
    post_dict = workflow.dump()
    session.set_responses(
        {"per_page": 1, "next": "", "response": [design_execution_dict]},
        {**post_dict, "status_description": "status"},
    )

    with pytest.raises(RuntimeError):
        collection_without_branch.update(workflow)


def test_update_with_mismatched_branch_root_ids(session, workflow, collection):
    # Given
    workflow.branch_root_id = uuid.uuid4()

    # Then/When
    with pytest.raises(ValueError):
        collection.update(workflow)


def test_update_model_missing_branch_root_id(
    session, workflow, collection_without_branch
):
    # Given
    workflow.branch_root_id = None

    # Then/When
    with pytest.raises(ValueError):
        collection_without_branch.update(workflow)


def test_update_model_missing_branch_version(
    session, workflow, collection_without_branch
):
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


def test_data_source_id(workflow):
    original_id = workflow.data_source_id
    assert workflow.data_source.to_data_source_id() == original_id
    workflow.data_source.table_version += 1
    assert workflow.data_source.to_data_source_id() != original_id
    assert workflow.data_source.to_data_source_id() == workflow.data_source_id

    workflow.data_source_id = None
    assert workflow.data_source_id is None
    assert workflow.data_source is None

    workflow.data_source_id = original_id
    assert workflow.data_source is not None
