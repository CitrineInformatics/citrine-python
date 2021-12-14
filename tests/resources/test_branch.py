import uuid
from datetime import datetime
from logging import getLogger

import pytest
from dateutil import tz

from citrine._rest.resource import ResourceTypeEnum
from citrine.resources.dataset import Dataset
from citrine.resources.branch import Branch, BranchCollection
from tests.utils.factories import BranchDataFactory
from tests.utils.session import FakeSession, FakeCall, FakePaginatedSession

logger = getLogger(__name__)


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def paginated_session() -> FakePaginatedSession:
    return FakePaginatedSession()


@pytest.fixture
def branch(session) -> Branch:
    branch = Branch(
        name='Test Branch',
        session=session
    )
    branch.uid = uuid.uuid4()
    return branch


@pytest.fixture
def collection(session) -> BranchCollection:
    return BranchCollection(
        project_id=uuid.uuid4(),
        session=session
    )


@pytest.fixture
def branch_path(collection) -> str:
    return BranchCollection._path_template.format(project_id=collection.project_id)


def test_str(branch):
    assert str(branch) == f'<Branch {branch.name!r}>'


def test_branch_build(collection, branch):
    new_branch = collection.build(branch.dump())

    assert new_branch.name == branch.name
    assert new_branch.created_at == branch.created_at
    assert new_branch.project_id == collection.project_id


def test_branch_register(session, collection, branch_path):
    # Given
    name = 'branch-name'
    now = datetime.now(tz.UTC).replace(microsecond=0)
    now_ms = int(now.timestamp() * 1000)  # ms since epoch
    branch_data = BranchDataFactory(
        name=name,
        created_at=now_ms,
        updated_at=now_ms
    )
    session.set_response(branch_data)

    # When
    new_branch = collection.register(Branch(name))

    # Then
    assert session.num_calls == 1
    expected_call = FakeCall(
        method='POST',
        path=branch_path,
        json={
            'name': name,
            'id': None
        }
    )
    assert expected_call == session.last_call
    assert new_branch.uid is not None
    assert new_branch.name == name
    assert new_branch.created_at == now
    assert new_branch.updated_at == now


def test_branch_get(session, collection, branch, branch_path):
    # Given
    branch_id = uuid.uuid4()
    session.set_response(branch.dump())

    # When
    branch = collection.get(branch_id)

    # Then
    assert session.num_calls == 1
    assert session.last_call == FakeCall(method='GET', path=f'{branch_path}/{branch_id}')


def test_branch_list(session, collection, branch_path):
    # Given
    branch_count = 5
    branches_data = BranchDataFactory.create_batch(branch_count)
    session.set_response({'response': branches_data})

    # When
    branches = list(collection.list())

    # Then
    assert session.num_calls == 1
    assert session.last_call == FakeCall(method='GET', path=branch_path, params={'per_page': 20})
    assert len(branches) == branch_count


def test_branch_delete(session, collection, branch_path):
    # Given
    branch_id = uuid.uuid4()

    # When
    response = collection.delete(branch_id)

    # Then
    assert session.num_calls == 1
    assert session.last_call == FakeCall(method='DELETE', path=f'{branch_path}/{branch_id}')


def test_branch_update(session, collection, branch, branch_path):
    # Given
    branch.name = "NEW NAME"
    session.set_response(branch.dump())

    # When
    updated_branch = collection.update(branch)

    # Then
    assert session.num_calls == 1
    expected_call = FakeCall(
        method='PUT',
        path=f'{branch_path}/{branch.uid}',
        json={
            'name': branch.name,
            'id': str(branch.uid)
        }
    )
    assert session.last_call == expected_call
    assert updated_branch.name == branch.name


def test_branch_get_design_workflows(branch):
    # Given
    branch.project_id = uuid.uuid4()

    # When
    dws = branch.design_workflows

    # Then
    assert dws.project_id == branch.project_id
    assert dws.branch_id == branch.uid


def test_branch_get_design_workflows_no_project_id(branch):
    with pytest.raises(AttributeError):
        branch.design_workflows


def test_branch_archive(session, collection, branch, branch_path):
    # When
    collection.archive(branch.uid)

    # Then
    assert session.num_calls == 1
    expected_path = f'{branch_path}/{branch.uid}/archive'
    assert session.last_call == FakeCall(method='PUT', path=expected_path, json={})


def test_branch_restore(session, collection, branch, branch_path):
    # When
    collection.restore(branch.uid)

    # Then
    assert session.num_calls == 1
    expected_path = f'{branch_path}/{branch.uid}/restore'
    assert session.last_call == FakeCall(method='PUT', path=expected_path, json={})


def test_branch_list_archived(session, collection, branch, branch_path):
    # Given
    branch_count = 5
    branches_data = BranchDataFactory.create_batch(branch_count)
    session.set_response({'response': branches_data})

    # When
    branches = list(collection.list_archived())

    # Then
    assert session.num_calls == 1
    assert session.last_call == FakeCall(method='GET', path=branch_path, params={'archived': True, 'per_page': 20})
