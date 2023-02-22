import uuid
from datetime import datetime
from logging import getLogger

import pytest
from dateutil import tz

from citrine._rest.resource import PredictorRef
from citrine.resources.data_version_update import NextBranchVersionRequest, DataVersionUpdate, BranchDataUpdate
from citrine.resources.branch import Branch, BranchCollection
from tests.utils.factories import BranchDataFactory, CandidateExperimentSnapshotDataFactory, \
    ExperimentDataSourceDataFactory, BranchDataFieldFactory, BranchMetadataFieldFactory, BranchDataUpdateFactory
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

    assert new_branch.name == branch_data["data"]["name"]
    assert new_branch.archived == branch_data["metadata"]["archived"]
    assert new_branch.project_id == collection.project_id


def test_branch_register(session, collection, branch_path):
    # Given
    root_id = str(uuid.uuid4())
    name = 'branch-name'
    now = datetime.now(tz.UTC).replace(microsecond=0)
    now_ms = int(now.timestamp() * 1000)  # ms since epoch
    branch_data = BranchDataFactory(data=BranchDataFieldFactory(name=name),
                                    metadata=BranchMetadataFieldFactory(
                                        created={
                                            'time': now_ms
                                        },
                                        updated={
                                            'time': now_ms
                                        }))
    session.set_response(branch_data)

    # When
    new_branch = collection.register(Branch(name))

    # Then
    assert session.num_calls == 1
    expected_call = FakeCall(
        method='POST',
        path=branch_path,
        json={
            'name': name
        },
        version="v2"
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
    assert session.last_call == FakeCall(method='GET', path=branch_path, params={'page': 1, 'per_page': 20})
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
            'name': branch_data['data']['name']
        },
        version='v2'
    )
    assert session.last_call == expected_call
    assert updated_branch.name == branch_data['data']['name']


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
    session.set_response(BranchDataFactory(metadata=BranchMetadataFieldFactory(archived=True)))

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
    session.set_response(BranchDataFactory(metadata=BranchMetadataFieldFactory(archived=False)))

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
    assert session.last_call == FakeCall(method='GET', path=branch_path, params={'archived': True, 'per_page': 20, 'page': 1})


# Needed for coverage checks
def test_branch_data_update_inits():
    data_updates = [DataVersionUpdate(current="gemd::16f91e7e-0214-4866-8d7f-a4d5c2125d2b::1",
                                      latest="gemd::16f91e7e-0214-4866-8d7f-a4d5c2125d2b::2")]
    predictors = [PredictorRef("aa971886-d17c-43b4-b602-5af7b44fcd5a", 2)]
    branch_update = BranchDataUpdate(data_updates=data_updates, predictors=predictors)
    assert branch_update.data_updates[0].current == "gemd::16f91e7e-0214-4866-8d7f-a4d5c2125d2b::1"


def test_branch_data_updates(session, collection, branch_path):
    # Given
    branch_id = uuid.uuid4()
    expected_data_updates = BranchDataUpdateFactory()
    session.set_response(expected_data_updates)

    # When
    actual_data_updates = collection.data_updates(branch_id)

    # Then
    expected_path = f'{branch_path}/{branch_id}/data-version-updates-predictor'
    assert session.last_call == FakeCall(method='GET',
                                         path=expected_path,
                                         version='v2')
    assert expected_data_updates['data_updates'][0]['current'] == actual_data_updates.data_updates[0].current
    assert expected_data_updates['data_updates'][0]['latest'] == actual_data_updates.data_updates[0].latest
    assert expected_data_updates['predictors'][0]['predictor_id'] == str(actual_data_updates.predictors[0].uid)


def test_branch_next_version(session, collection, branch_path):
    # Given
    branch_data = BranchDataFactory()
    root_branch_id = branch_data['metadata']['root_id']
    session.set_response(branch_data)
    data_updates = [DataVersionUpdate(current="gemd::16f91e7e-0214-4866-8d7f-a4d5c2125d2b::1",
                                      latest="gemd::16f91e7e-0214-4866-8d7f-a4d5c2125d2b::2")]
    predictors = [PredictorRef("aa971886-d17c-43b4-b602-5af7b44fcd5a", 2)]
    req = NextBranchVersionRequest(data_updates=data_updates, use_predictors=predictors)

    # When
    branchv2 = collection.next_version(root_branch_id, branch_instructions=req, retrain_models=False)

    # Then
    expected_path = f'{branch_path}/next-version-predictor'
    expected_call = FakeCall(method='POST',
                             path=expected_path,
                             params={'root': str(root_branch_id),
                                     'retrain_models': False},
                             json={
                                 'data_updates': [
                                     {
                                         'current': 'gemd::16f91e7e-0214-4866-8d7f-a4d5c2125d2b::1',
                                         'latest': 'gemd::16f91e7e-0214-4866-8d7f-a4d5c2125d2b::2',
                                         'type': 'DataVersionUpdate'
                                     }
                                 ],
                                 'use_predictors': [
                                     {
                                         'predictor_id': 'aa971886-d17c-43b4-b602-5af7b44fcd5a',
                                         'predictor_version': 2
                                     }
                                 ]
                             },
                             version='v2')
    assert session.last_call == expected_call
    assert str(branchv2.root_id) == root_branch_id


def test_branch_data_updates_normal(session, collection, branch_path):
    # Given
    branch_data = BranchDataFactory()
    root_branch_id = branch_data['metadata']['root_id']
    session.set_response(branch_data)

    branch = collection.get(branch_data['id'])

    data_updates = BranchDataUpdateFactory()
    v2branch_data = BranchDataFactory(metadata=BranchMetadataFieldFactory(root_id=root_branch_id))
    session.set_responses(data_updates, v2branch_data)
    v2branch = collection.update_data(branch)

    # Then
    expected_path = f'{branch_path}/next-version-predictor'
    expected_call = FakeCall(method='POST',
                             path=expected_path,
                             params={'root': str(root_branch_id),
                                     'retrain_models': False},
                             json={
                                 'data_updates': [
                                     {
                                         'current': data_updates['data_updates'][0]['current'],
                                         'latest': data_updates['data_updates'][0]['latest'],
                                         'type': 'DataVersionUpdate'
                                     }
                                 ],
                                 'use_predictors': [
                                     {
                                         'predictor_id': data_updates['predictors'][0]['predictor_id'],
                                         'predictor_version': data_updates['predictors'][0]['predictor_version']
                                     }
                                 ]
                             },
                             version='v2')
    assert session.last_call == expected_call
    assert str(v2branch.root_id) == root_branch_id


def test_branch_data_updates_latest(session, collection, branch_path):
    # Given
    branch_data = BranchDataFactory()
    root_branch_id = branch_data['metadata']['root_id']
    session.set_response(branch_data)

    branch = collection.get(branch_data['id'])
    print(branch)

    data_updates = BranchDataUpdateFactory()
    v2branch_data = BranchDataFactory(metadata=BranchMetadataFieldFactory(root_id=root_branch_id))
    session.set_responses(data_updates, v2branch_data)
    v2branch = collection.update_data(branch, use_existing=False, retrain_models=True)

    # Then
    expected_path = f'{branch_path}/next-version-predictor'
    expected_call = FakeCall(method='POST',
                             path=expected_path,
                             params={'root': str(root_branch_id),
                                     'retrain_models': True},
                             json={
                                 'data_updates': [
                                     {
                                         'current': data_updates['data_updates'][0]['current'],
                                         'latest': data_updates['data_updates'][0]['latest'],
                                         'type': 'DataVersionUpdate'
                                     }
                                 ],
                                 'use_predictors': []
                             },
                             version='v2')
    assert session.last_call == expected_call
    assert str(v2branch.root_id) == root_branch_id


def test_branch_data_updates_nochange(session, collection, branch_path):
    # Given
    branch_data = BranchDataFactory()
    session.set_response(branch_data)

    branch = collection.get(branch_data['id'])
    print(branch)

    data_updates = BranchDataUpdateFactory(data_updates=[], predictors=[])
    session.set_responses(branch_data, data_updates)
    v2branch = collection.update_data(branch.uid)

    assert v2branch == None


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
        FakeCall(method='GET', path=erds_path, params={'branch': branch.uid, 'version': 'latest', 'per_page': 100, 'page': 1})
    ]


def test_no_experiment_datasource(session, collection):
    # Given
    erds_path = f'projects/{collection.project_id}/candidate-experiment-datasources'
    branch = collection.build(BranchDataFactory())
    session.set_response({'response': []})

    # When / Then
    assert branch.experiment_datasource is None
    assert session.calls == [
        FakeCall(method='GET', path=erds_path, params={'branch': branch.uid, 'version': 'latest', 'per_page': 100, 'page': 1})
    ]


def test_experiment_data_source_no_project_id(session):
    branch = BranchCollection(None, session).build(BranchDataFactory())
    with pytest.raises(AttributeError):
        branch.experiment_datasource

    assert not session.calls
