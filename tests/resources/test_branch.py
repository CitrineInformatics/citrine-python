import uuid
from datetime import datetime
from logging import getLogger

import pytest
from dateutil import tz

from citrine._rest.resource import ResourceTypeEnum
from citrine.resources.dataset import Dataset
from citrine.resources.branch import Branch, BranchCollection
from tests.utils.factories import BranchDataFactory, CandidateExperimentSnapshotDataFactory, ExperimentDataSourceDataFactory
from tests.utils.session import FakeSession, FakeCall, FakePaginatedSession

logger = getLogger(__name__)


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def paginated_session() -> FakePaginatedSession:
    return FakePaginatedSession()


@pytest.fixture
def collection(session) -> BranchCollection:
    return BranchCollection(
        project_id=uuid.uuid4(),
        session=session
    )


@pytest.fixture
def branch_path(collection) -> str:
    return BranchCollection._path_template.format(project_id=collection.project_id)


def test_str():
    name = "Test Branch name"
    branch = Branch(name=name)
    assert str(branch) == f'<Branch {name!r}>'


def test_branch_build(collection):
    branch_data = BranchDataFactory()
    new_branch = collection.build(branch_data)

    assert new_branch.name == branch_data["name"]
    assert new_branch.archived == branch_data["archived"]
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


def test_branch_get(session, collection, branch_path):
    # Given
    branch_data = BranchDataFactory()
    session.set_response(branch_data)

    # When
    branch = collection.get(branch_data['id'])

    # Then
    assert session.num_calls == 1
    assert session.last_call == FakeCall(method='GET', path=f'{branch_path}/{branch_data["id"]}')


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


def test_branch_update(session, collection, branch_path):
    # Given
    branch_data = BranchDataFactory()
    session.set_response(branch_data)

    # When
    updated_branch = collection.update(Branch.build(branch_data))

    # Then
    assert session.num_calls == 1
    expected_call = FakeCall(
        method='PUT',
        path=f'{branch_path}/{branch_data["id"]}',
        json={
            'name': branch_data['name'],
            'id': str(branch_data['id'])
        }
    )
    assert session.last_call == expected_call
    assert updated_branch.name == branch_data['name']


def test_branch_get_design_workflows(collection):
    # Given
    branch = collection.build(BranchDataFactory())

    # When
    dws = branch.design_workflows

    # Then
    assert dws.project_id == branch.project_id
    assert dws.branch_id == branch.uid


def test_branch_get_design_workflows_no_project_id(session):
    branch = BranchCollection(None, session).build(BranchDataFactory())
    with pytest.raises(AttributeError):
        branch.design_workflows


def test_branch_archive(session, collection, branch_path):
    # Given
    branch_id = uuid.uuid4()
    session.set_response(BranchDataFactory(archived=True))

    # When
    archived_branch = collection.archive(branch_id)

    # Then
    assert session.num_calls == 1
    expected_path = f'{branch_path}/{branch_id}/archive'
    assert session.last_call == FakeCall(method='PUT', path=expected_path, json={})
    assert archived_branch.archived is True


def test_branch_restore(session, collection, branch_path):
    # Given
    branch_id = uuid.uuid4()
    session.set_response(BranchDataFactory(archived=False))

    # When
    restored_branch = collection.restore(branch_id)

    # Then
    assert session.num_calls == 1
    expected_path = f'{branch_path}/{branch_id}/restore'
    assert session.last_call == FakeCall(method='PUT', path=expected_path, json={})
    assert restored_branch.archived is False


def test_branch_list_archived(session, collection, branch_path):
    # Given
    branch_count = 5
    branches_data = BranchDataFactory.create_batch(branch_count)
    session.set_response({'response': branches_data})

    # When
    branches = list(collection.list_archived())

    # Then
    assert session.num_calls == 1
    assert session.last_call == FakeCall(method='GET', path=branch_path, params={'archived': True, 'per_page': 20})


def test_experiment_datasource(session, collection):
    # Given
    erds_path = f'projects/{collection.project_id}/candidate-experiment-datasources'

    erds = ExperimentDataSourceDataFactory()
    erds['data']['experiments'] = [CandidateExperimentSnapshotDataFactory()]

    branch = collection.build(BranchDataFactory())
    session.set_response({'response': [erds]})


    # When / Then
    assert branch.experiment_datasource is not None
    assert session.calls == [
        FakeCall(method='GET', path=erds_path, params={'branch': branch.uid, 'version': 'latest', 'per_page': 100})
    ]


def test_no_experiment_datasource(session, collection):
    # Given
    erds_path = f'projects/{collection.project_id}/candidate-experiment-datasources'
    branch = collection.build(BranchDataFactory())
    session.set_response({'response': []})

    # When / Then
    assert branch.experiment_datasource is None
    assert session.calls == [
        FakeCall(method='GET', path=erds_path, params={'branch': branch.uid, 'version': 'latest', 'per_page': 100})
    ]


def test_experiment_data_source_no_project_id(session):
    branch = BranchCollection(None, session).build(BranchDataFactory())
    with pytest.raises(AttributeError):
        branch.experiment_datasource

    assert not session.calls
