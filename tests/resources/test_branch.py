import uuid
from datetime import datetime
from logging import getLogger

import pytest
from dateutil import tz

from citrine._rest.resource import PredictorRef
from citrine.exceptions import NotFound
from citrine.resources.data_version_update import NextBranchVersionRequest, DataVersionUpdate, BranchDataUpdate
from citrine.resources.branch import Branch, BranchCollection
from tests.utils.factories import BranchDataFactory, BranchRootDataFactory, \
    CandidateExperimentSnapshotDataFactory, ExperimentDataSourceDataFactory, \
    BranchDataFieldFactory, BranchMetadataFieldFactory, BranchDataUpdateFactory
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
    root_id = branch_data['metadata']['root_id']
    version = branch_data['metadata']['version']
    session.set_response({"response": [branch_data]})

    # When
    branch = collection.get(root_id=root_id, version=version)

    # Then
    assert session.num_calls == 1
    assert session.last_call == FakeCall(method='GET', path=branch_path, params={'page': 1, 'per_page': 1, 'root': root_id, 'version': version})


def test_branch_list(session, collection, branch_path):
    # Given
    branch_count = 5
    branches_data = BranchDataFactory.create_batch(branch_count)
    session.set_response({'response': branches_data})

    # When
    with pytest.deprecated_call():
        branches = list(collection.list())

    # Then
    assert session.num_calls == 1
    assert session.last_call == FakeCall(method='GET', path=branch_path, params={'page': 1, 'per_page': 20})
    assert len(branches) == branch_count


def test_branch_list_all(session, collection, branch_path):
    # Given
    branch_count = 5
    branches_data = BranchDataFactory.create_batch(branch_count)
    session.set_response({'response': branches_data})

    # When
    branches = list(collection.list_all())

    # Then
    assert session.num_calls == 1
    assert session.last_call == FakeCall(method='GET', path=branch_path, params={'per_page': 20, 'page': 1})




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
    assert dws.branch_root_id == branch.root_id
    assert dws.branch_version == branch.version


def test_branch_get_design_workflows_no_project_id(session):
    branch = BranchCollection(None, session).build(BranchDataFactory())
    with pytest.raises(AttributeError):
        branch.design_workflows


def test_branch_archive(session, collection, branch_path):
    # Given
    branch_data = BranchDataFactory(metadata=BranchMetadataFieldFactory(archived=True))
    branch_id = branch_data['id']
    root_id = branch_data['metadata']['root_id']
    version = branch_data['metadata']['version']
    branch_data_get_resp = {"response": [branch_data]}
    branch_data_get_params = {
        'page': 1, 'per_page': 1, 'root': str(root_id), 'version': version
    }
    session.set_responses(branch_data_get_resp, branch_data)

    # When
    archived_branch = collection.archive(root_id=root_id, version=version)

    # Then
    expected_path = f'{branch_path}/{branch_id}/archive'
    assert session.calls == [
        FakeCall(method='GET', path=branch_path, params=branch_data_get_params),
        FakeCall(method='PUT', path=expected_path, json={})
    ]
    assert archived_branch.archived is True


def test_archive_version_omitted(session, collection, branch_path):
    # Given
    branch_data = BranchDataFactory(metadata=BranchMetadataFieldFactory(archived=True))
    branch_id = branch_data['id']
    root_id = branch_data['metadata']['root_id']
    branch_data_get_resp = {"response": [branch_data]}
    branch_data_get_params = {
        'page': 1, 'per_page': 1, 'root': str(root_id), 'version': 'latest'
    }
    session.set_responses(branch_data_get_resp, branch_data)

    # When
    archived_branch = collection.archive(root_id=root_id)

    # Then
    expected_path = f'{branch_path}/{branch_id}/archive'
    assert session.calls == [
        FakeCall(method='GET', path=branch_path, params=branch_data_get_params),
        FakeCall(method='PUT', path=expected_path, json={})
    ]
    assert archived_branch.archived is True


def test_branch_restore(session, collection, branch_path):
    # Given
    branch_data = BranchDataFactory(metadata=BranchMetadataFieldFactory(archived=False))
    branch_id = branch_data['id']
    root_id = branch_data['metadata']['root_id']
    version = branch_data['metadata']['version']
    branch_data_get_resp = {"response": [branch_data]}
    branch_data_get_params = {
        'page': 1, 'per_page': 1, 'root': str(root_id), 'version': version
    }
    session.set_responses(branch_data_get_resp, branch_data)

    # When
    restored_branch = collection.restore(root_id=root_id, version=version)

    # Then
    expected_path = f'{branch_path}/{branch_id}/restore'
    assert session.calls == [
        FakeCall(method='GET', path=branch_path, params=branch_data_get_params),
        FakeCall(method='PUT', path=expected_path, json={})
    ]
    assert restored_branch.archived is False


def test_restore_version_omitted(session, collection, branch_path):
    # Given
    branch_data = BranchDataFactory(metadata=BranchMetadataFieldFactory(archived=False))
    branch_id = branch_data['id']
    root_id = branch_data['metadata']['root_id']
    branch_data_get_resp = {"response": [branch_data]}
    branch_data_get_params = {
        'page': 1, 'per_page': 1, 'root': str(root_id), 'version': 'latest'
    }
    session.set_responses(branch_data_get_resp, branch_data)

    # When
    restored_branch = collection.restore(root_id=root_id)

    # Then
    expected_path = f'{branch_path}/{branch_id}/restore'
    assert session.calls == [
        FakeCall(method='GET', path=branch_path, params=branch_data_get_params),
        FakeCall(method='PUT', path=expected_path, json={})
    ]
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
    branch_data = BranchDataFactory()
    root_branch_id = branch_data['metadata']['root_id']
    branch_id = branch_data['id']
    expected_data_updates = BranchDataUpdateFactory()
    branch_data_get_resp = {"response": [branch_data]}
    branch_data_get_params = {
        'page': 1, 'per_page': 1, 'root': str(root_branch_id), 'version': branch_data['metadata']['version']
    }
    session.set_responses(branch_data_get_resp, expected_data_updates)

    # When
    actual_data_updates = collection.data_updates(root_id=root_branch_id, version=branch_data['metadata']['version'])

    # Then
    expected_path = f'{branch_path}/{branch_id}/data-version-updates-predictor'
    assert session.calls == [
        FakeCall(method='GET', path=branch_path, params=branch_data_get_params),
        FakeCall(method='GET', path=expected_path, version='v2')
    ]
    assert expected_data_updates['data_updates'][0]['current'] == actual_data_updates.data_updates[0].current
    assert expected_data_updates['data_updates'][0]['latest'] == actual_data_updates.data_updates[0].latest
    assert expected_data_updates['predictors'][0]['predictor_id'] == str(actual_data_updates.predictors[0].uid)


def test_data_updates_version_omitted(session, collection, branch_path):
    # Given
    branch_data = BranchDataFactory()
    root_branch_id = branch_data['metadata']['root_id']
    branch_id = branch_data['id']
    expected_data_updates = BranchDataUpdateFactory()
    branch_data_get_resp = {"response": [branch_data]}
    branch_data_get_params = {
        'page': 1, 'per_page': 1, 'root': str(root_branch_id), 'version': branch_data['metadata']['version']
    }
    session.set_responses(branch_data_get_resp, expected_data_updates)

    # When
    actual_data_updates = collection.data_updates(root_id=root_branch_id, version=branch_data['metadata']['version'])

    # Then
    expected_path = f'{branch_path}/{branch_id}/data-version-updates-predictor'
    assert session.calls == [
        FakeCall(method='GET', path=branch_path, params=branch_data_get_params),
        FakeCall(method='GET', path=expected_path, version='v2')
    ]
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
    branchv2 = collection.next_version(root_id=root_branch_id, branch_instructions=req, retrain_models=False)

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
    assert session.num_calls == 1
    assert session.last_call == expected_call
    assert str(branchv2.root_id) == root_branch_id


def test_branch_data_updates_normal(session, collection, branch_path):
    # Given
    branch_data = BranchDataFactory()
    root_branch_id = branch_data["metadata"]["root_id"]
    branch_data_get_resp = {"response": [branch_data]}
    branch_data_get_params = {
        'page': 1, 'per_page': 1, 'root': str(root_branch_id), 'version': branch_data['metadata']['version']
    }

    session.set_response(branch_data_get_resp)

    branch = collection.get(root_id=root_branch_id, version=branch_data['metadata']['version'])

    data_updates = BranchDataUpdateFactory()
    v2branch_data = BranchDataFactory(metadata=BranchMetadataFieldFactory(root_id=root_branch_id))
    session.set_responses(branch_data_get_resp, data_updates, v2branch_data)
    v2branch = collection.update_data(root_id=branch.root_id, version=branch.version)

    # Then
    next_version_call = FakeCall(method='POST',
                                 path=f'{branch_path}/next-version-predictor',
                                 params={'root': str(root_branch_id), 'retrain_models': False},
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
    assert session.calls == [
        FakeCall(method='GET', path=branch_path, params=branch_data_get_params),
        FakeCall(method='GET', path=branch_path, params=branch_data_get_params),
        FakeCall(method='GET', path=f'{branch_path}/{branch_data["id"]}/data-version-updates-predictor'),
        next_version_call
    ]
    assert str(v2branch.root_id) == root_branch_id


def test_branch_data_updates_latest(session, collection, branch_path):
    # Given
    branch_data = BranchDataFactory()
    root_branch_id = branch_data['metadata']['root_id']
    branch_data_get_resp = {"response": [branch_data]}
    branch_data_get_params = {
        'page': 1, 'per_page': 1, 'root': str(root_branch_id), 'version': branch_data['metadata']['version']
    }
    session.set_response(branch_data_get_resp)

    branch = collection.get(root_id=root_branch_id, version=branch_data['metadata']['version'])

    data_updates = BranchDataUpdateFactory()
    v2branch_data = BranchDataFactory(metadata=BranchMetadataFieldFactory(root_id=root_branch_id))
    session.set_responses(branch_data_get_resp, data_updates, v2branch_data)
    v2branch = collection.update_data(root_id=branch.root_id, version=branch.version, use_existing=False, retrain_models=True)

    # Then
    next_version_call = FakeCall(method='POST',
                             path=f'{branch_path}/next-version-predictor',
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
    assert session.calls == [
        FakeCall(method='GET', path=branch_path, params=branch_data_get_params),
        FakeCall(method='GET', path=branch_path, params=branch_data_get_params),
        FakeCall(method='GET', path=f'{branch_path}/{branch_data["id"]}/data-version-updates-predictor'),
        next_version_call
    ]
    assert str(v2branch.root_id) == root_branch_id


def test_branch_data_updates_nochange(session, collection, branch_path):
    # Given
    branch_data = BranchDataFactory()
    branch_data_get_resp = {"response": [branch_data]}
    session.set_response(branch_data_get_resp)

    branch = collection.get(root_id=branch_data['metadata']['root_id'], version=branch_data['metadata']['version'])

    data_updates = BranchDataUpdateFactory(data_updates=[], predictors=[])
    session.set_responses(branch_data_get_resp, data_updates)
    v2branch = collection.update_data(root_id=branch.root_id, version=branch.version)

    assert v2branch is None


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
        FakeCall(method='GET', path=erds_path, params={'branch': str(branch.uid), 'version': 'latest', 'per_page': 100, 'page': 1})
    ]


def test_no_experiment_datasource(session, collection):
    # Given
    erds_path = f'projects/{collection.project_id}/candidate-experiment-datasources'
    branch = collection.build(BranchDataFactory())
    session.set_response({'response': []})

    # When / Then
    assert branch.experiment_datasource is None
    assert session.calls == [
        FakeCall(method='GET', path=erds_path, params={'branch': str(branch.uid), 'version': 'latest', 'per_page': 100, 'page': 1})
    ]


def test_experiment_data_source_no_project_id(session):
    branch = BranchCollection(None, session).build(BranchDataFactory())
    with pytest.raises(AttributeError):
        branch.experiment_datasource

    assert not session.calls


def test_get_by_root_id_deprecated(session, collection, branch_path):
    # Given
    branches_data = BranchDataFactory.create_batch(1)
    session.set_response({'response': branches_data})
    root_id = uuid.uuid4()

    # When
    with pytest.deprecated_call():
        branch = collection.get_by_root_id(branch_root_id=root_id)

    # Then
    assert session.calls == [FakeCall(
        method='GET',
        path=branch_path,
        params={'page': 1, 'per_page': 1, 'root': str(root_id), 'version': 'latest'}
    )]


def test_get_by_root_id_not_found_deprecated(session, collection, branch_path):
    # Given
    session.set_response({'response': []})
    root_id = uuid.uuid4()

    # When
    with pytest.deprecated_call():
        with pytest.raises(NotFound) as exc:
            collection.get_by_root_id(branch_root_id=root_id)

    # Then
    assert str(root_id) in str(exc)
    assert "branch root" in str(exc).lower()
    assert "latest" in str(exc).lower()


def test_branch_data_updates_normal_deprecated(session, collection, branch_path):
    # Given
    branch_data = BranchDataFactory()
    root_branch_id = branch_data["metadata"]["root_id"]
    branch_data_get_resp = {"response": [branch_data]}
    branch_data_get_params = {
        'page': 1, 'per_page': 1, 'root': str(root_branch_id), 'version': branch_data['metadata']['version']
    }
    session.set_response(branch_data)

    with pytest.deprecated_call():
        branch = collection.get(branch_data['id'])

    data_updates = BranchDataUpdateFactory()
    v2branch_data = BranchDataFactory(metadata=BranchMetadataFieldFactory(root_id=root_branch_id))
    session.set_responses(branch_data_get_resp, data_updates, v2branch_data)
    with pytest.deprecated_call():
        v2branch = collection.update_data(branch)

    # Then
    next_version_call = FakeCall(method='POST',
                             path=f'{branch_path}/next-version-predictor',
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
    assert session.calls == [
        FakeCall(method='GET', path=f'{branch_path}/{branch_data["id"]}'),
        FakeCall(method='GET', path=branch_path, params=branch_data_get_params),
        FakeCall(method='GET', path=f'{branch_path}/{branch_data["id"]}/data-version-updates-predictor'),
        next_version_call
    ]
    assert str(v2branch.root_id) == root_branch_id


def test_branch_data_updates_latest_deprecated(session, collection, branch_path):
    # Given
    branch_data = BranchDataFactory()
    root_branch_id = branch_data['metadata']['root_id']
    branch_data_get_resp = {"response": [branch_data]}
    branch_data_get_params = {
        'page': 1, 'per_page': 1, 'root': str(root_branch_id), 'version': branch_data['metadata']['version']
    }
    session.set_response(branch_data)

    with pytest.deprecated_call():
        branch = collection.get(branch_data['id'])

    data_updates = BranchDataUpdateFactory()
    v2branch_data = BranchDataFactory(metadata=BranchMetadataFieldFactory(root_id=root_branch_id))
    session.set_responses(branch_data_get_resp, data_updates, v2branch_data)
    with pytest.deprecated_call():
        v2branch = collection.update_data(branch, use_existing=False, retrain_models=True)

    # Then
    next_version_call = FakeCall(method='POST',
                             path=f'{branch_path}/next-version-predictor',
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
    assert session.calls == [
        FakeCall(method='GET', path=f'{branch_path}/{branch_data["id"]}'),
        FakeCall(method='GET', path=branch_path, params=branch_data_get_params),
        FakeCall(method='GET', path=f'{branch_path}/{branch_data["id"]}/data-version-updates-predictor'),
        next_version_call
    ]
    assert str(v2branch.root_id) == root_branch_id


def test_branch_data_updates_nochange_deprecated(session, collection, branch_path):
    # Given
    branch_data = BranchDataFactory()
    branch_data_get_resp = {"response": [branch_data]}
    session.set_response(branch_data)

    with pytest.deprecated_call():
        branch = collection.get(branch_data['id'])

    data_updates = BranchDataUpdateFactory(data_updates=[], predictors=[])
    session.set_responses(branch_data, branch_data_get_resp, data_updates)
    with pytest.deprecated_call():
        v2branch = collection.update_data(branch.uid)

    assert v2branch is None


def test_branch_get_deprecated(session, collection, branch_path):
    # Given
    branch_data = BranchDataFactory()
    session.set_response(branch_data)

    # When
    with pytest.deprecated_call():
        branch = collection.get(branch_data['id'])

    # Then
    assert session.num_calls == 1
    assert session.last_call == FakeCall(method='GET', path=f'{branch_path}/{branch_data["id"]}')


def test_branch_archive_deprecated(session, collection, branch_path):
    # Given
    branch_id = uuid.uuid4()
    session.set_response(BranchDataFactory(metadata=BranchMetadataFieldFactory(archived=True)))

    # When
    with pytest.deprecated_call():
        archived_branch = collection.archive(branch_id)

    # Then
    assert session.num_calls == 1
    expected_path = f'{branch_path}/{branch_id}/archive'
    assert session.last_call == FakeCall(method='PUT', path=expected_path, json={})
    assert archived_branch.archived is True


def test_branch_restore_deprecated(session, collection, branch_path):
    # Given
    branch_id = uuid.uuid4()
    session.set_response(BranchDataFactory(metadata=BranchMetadataFieldFactory(archived=False)))

    # When
    with pytest.deprecated_call():
        restored_branch = collection.restore(branch_id)

    # Then
    assert session.num_calls == 1
    expected_path = f'{branch_path}/{branch_id}/restore'
    assert session.last_call == FakeCall(method='PUT', path=expected_path, json={})
    assert restored_branch.archived is False


def test_branch_data_updates_deprecated(session, collection, branch_path):
    # Given
    branch_id = uuid.uuid4()
    expected_data_updates = BranchDataUpdateFactory()
    session.set_response(expected_data_updates)

    # When
    with pytest.deprecated_call():
        actual_data_updates = collection.data_updates(branch_id)

    # Then
    assert session.num_calls == 1
    expected_path = f'{branch_path}/{branch_id}/data-version-updates-predictor'
    assert session.last_call == FakeCall(method='GET',
                                         path=expected_path,
                                         version='v2')
    assert expected_data_updates['data_updates'][0]['current'] == actual_data_updates.data_updates[0].current
    assert expected_data_updates['data_updates'][0]['latest'] == actual_data_updates.data_updates[0].latest
    assert expected_data_updates['predictors'][0]['predictor_id'] == str(actual_data_updates.predictors[0].uid)


def test_branch_next_version_deprecated(session, collection, branch_path):
    # Given
    branch_data = BranchDataFactory()
    root_branch_id = branch_data['metadata']['root_id']
    session.set_response(branch_data)
    data_updates = [DataVersionUpdate(current="gemd::16f91e7e-0214-4866-8d7f-a4d5c2125d2b::1",
                                      latest="gemd::16f91e7e-0214-4866-8d7f-a4d5c2125d2b::2")]
    predictors = [PredictorRef("aa971886-d17c-43b4-b602-5af7b44fcd5a", 2)]
    req = NextBranchVersionRequest(data_updates=data_updates, use_predictors=predictors)

    # When
    with pytest.deprecated_call():
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
    assert session.num_calls == 1
    assert session.last_call == expected_call
    assert str(branchv2.root_id) == root_branch_id


def test_get_both_ids(collection):
    with pytest.deprecated_call():
        with pytest.raises(ValueError):
            collection.get(uuid.uuid4(), root_id=uuid.uuid4())


def test_get_neither_id(collection):
    with pytest.raises(ValueError):
        collection.get()


def test_archive_neither_id(collection):
    with pytest.raises(ValueError):
        collection.archive()


def test_restore_neither_id(collection):
    with pytest.raises(ValueError):
        collection.restore()


def test_update_data_both_ids(collection):
    with pytest.raises(ValueError):
        collection.update_data(uuid.uuid4(), root_id=uuid.uuid4())


def test_update_data_neither_id(collection):
    with pytest.raises(ValueError):
        collection.update_data()


def test_data_updates_both_ids(collection):
    with pytest.deprecated_call():
        with pytest.raises(ValueError):
            collection.data_updates(uuid.uuid4(), root_id=uuid.uuid4())


def test_data_updates_neither_id(collection):
    with pytest.raises(ValueError):
        collection.data_updates()
