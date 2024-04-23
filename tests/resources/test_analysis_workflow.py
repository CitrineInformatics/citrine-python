import random
import uuid
from datetime import datetime, timezone

import pytest

from citrine.informatics.workflows.analysis_workflow import AnalysisWorkflow
from citrine.resources.analysis_workflow import AnalysisWorkflowCollection

from tests.utils.factories import AnalysisWorkflowEntityDataFactory
from tests.utils.session import FakeCall, FakeSession


def paging_response(*items):
    return {"response": items}


def _assert_user_timestamp_equals_dict(user, time, ut_dict):
    assert str(user) == ut_dict['user']
    assert time == datetime.fromtimestamp(ut_dict['time'] / 1000, tz=timezone.utc)


def _assert_aw_plot_equals_dict(plot, plot_dict):
    # Presently, plots are just raw JSON, so we can compare them directly.
    assert plot == plot_dict


def _assert_aw_equals_dict(aw, aw_dict):
    assert str(aw.uid) == aw_dict['id']
    assert aw.name == aw_dict['data']['name']
    assert aw.description == aw_dict['data']['description']
    snapshot_id_dict = aw_dict['data'].get('snapshot_id')
    if snapshot_id_dict:
        assert str(aw.snapshot_id) == snapshot_id_dict
    else:
        assert aw.snapshot_id is None

    _assert_user_timestamp_equals_dict(aw.created_by, aw.create_time, aw_dict['metadata']['created'])
    _assert_user_timestamp_equals_dict(aw.updated_by, aw.update_time, aw_dict['metadata']['updated'])
    
    aw_dict_latest_build = aw_dict['metadata'].get('latest_build') or {}
    if aw_dict_latest_build:
        assert aw.latest_build.status == aw_dict_latest_build['status']
        assert aw.latest_build.failures == aw_dict_latest_build['failure_reason']
        assert aw.status == aw_dict_latest_build['status']
    else:
        assert aw.latest_build is None

    aw_dict_archived = aw_dict['metadata'].get('archived') or {}
    if aw_dict_archived:
        _assert_user_timestamp_equals_dict(aw.archived_by, aw.archive_time, aw_dict_archived)
    else:
        assert aw.archived_by is None
        assert aw.archive_time is None

    for plot, plot_dict in zip(aw.plots, aw_dict['data'].get('plots')):
        _assert_aw_plot_equals_dict(plot, plot_dict)


@pytest.fixture
def session():
    return FakeSession()

@pytest.fixture
def team_id():
    return uuid.uuid4()

@pytest.fixture
def collection(session, team_id):
    return AnalysisWorkflowCollection(session, team_id=team_id)

@pytest.fixture
def base_path(team_id):
    return f'/teams/{team_id}/analysis-workflows'


def test_register(session, collection, base_path):
    aw_data = AnalysisWorkflowEntityDataFactory(data__plot_count=3)
    session.set_response(aw_data)

    aw_module = AnalysisWorkflow(**aw_data['data'])

    aw = collection.register(aw_module)

    expected_payload = {
        **aw_data['data'],
        "plots": [plot['data'] for plot in aw_data['data']['plots']]
    }
    assert session.calls == [FakeCall(method='POST', path=base_path, json=expected_payload)]
    _assert_aw_equals_dict(aw, aw_data)


def test_get(session, collection, base_path):
    aw_data = AnalysisWorkflowEntityDataFactory()
    session.set_response(aw_data)
    
    aw = collection.get(aw_data['id'])

    assert session.calls == [FakeCall(method='GET', path=f'{base_path}/{aw_data["id"]}')]
    _assert_aw_equals_dict(aw, aw_data)


def test_list_all(session, collection, base_path):
    aw_data = [AnalysisWorkflowEntityDataFactory(metadata__is_archived=random.choice((True, False))) for _ in range(5)]
    session.set_response(paging_response(*aw_data))
    
    aws = list(collection.list_all())

    expected_call = FakeCall(method='GET', path=base_path, params={'page': 1, 'per_page': 20, 'include_archived': True})
    assert session.calls == [expected_call]
    assert len(aws) == len(aw_data)


def test_list_archived(session, collection, base_path):
    aw_data = [AnalysisWorkflowEntityDataFactory(metadata__is_archived=False) for _ in range(3)]
    session.set_response(paging_response(*aw_data))
    
    aws = list(collection.list_archived(per_page=50))

    expected_call = FakeCall(method='GET', path=base_path, params={'page': 1, 'per_page': 50, 'filter': "archived eq 'true'"})
    assert session.calls == [expected_call]
    assert len(aws) == len(aw_data)


def test_list(session, collection, base_path):
    aw_data = [AnalysisWorkflowEntityDataFactory(metadata__is_archived=False) for _ in range(3)]
    session.set_responses(paging_response(*aw_data[0:2]), paging_response(*aw_data[2:4]))
    
    aws = list(collection.list(per_page=2))

    expected_calls = [
        FakeCall(method='GET', path=base_path, params={'page': 1, 'per_page': 2, 'filter': "archived eq 'false'"}),
        FakeCall(method='GET', path=base_path, params={'page': 2, 'per_page': 2, 'filter': "archived eq 'false'"})
    ]
    assert session.calls == expected_calls
    assert len(aws) == len(aw_data)


def test_archive(session, collection, base_path):
    aw_data = AnalysisWorkflowEntityDataFactory(metadata__is_archived=True)
    session.set_response(aw_data)
    
    aw = collection.archive(aw_data['id'])

    assert session.calls == [FakeCall(method='PUT', path=f'{base_path}/{aw_data["id"]}/archive', json={})]
    _assert_aw_equals_dict(aw, aw_data)


def test_restore(session, collection, base_path):
    aw_data = AnalysisWorkflowEntityDataFactory(metadata__is_archived=False)
    session.set_response(aw_data)
    
    aw = collection.restore(aw_data['id'])

    assert session.calls == [FakeCall(method='PUT', path=f'{base_path}/{aw_data["id"]}/restore', json={})]
    _assert_aw_equals_dict(aw, aw_data)


def test_update(session, collection, base_path):
    aw_data = AnalysisWorkflowEntityDataFactory(metadata__is_archived=False)
    session.set_response(aw_data)
    
    name, description = aw_data['data']['name'], aw_data['data']['description']
    
    aw = collection.update(aw_data['id'], name=name, description=description)

    expected_payload = {"name": name, "description": description}
    assert session.calls == [FakeCall(method='PUT', path=f'{base_path}/{aw_data["id"]}', json=expected_payload)] 
    _assert_aw_equals_dict(aw, aw_data)


def test_rebuild(session, collection, base_path):
    aw_data = AnalysisWorkflowEntityDataFactory(data__has_snapshot=True, metadata__has_build=True)
    session.set_response(aw_data)
    
    aw = collection.rebuild(aw_data['id'])

    assert session.calls == [FakeCall(method='PUT', path=f'{base_path}/{aw_data["id"]}/query/rerun', json={})]
    _assert_aw_equals_dict(aw, aw_data)


def test_delete_unsupported(session, collection, base_path):
    with pytest.raises(NotImplementedError):
        collection.delete(uuid.uuid4())
