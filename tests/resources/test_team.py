import json
import uuid
from uuid import UUID

import pytest
from dateutil.parser import parse
from gemd.entity.link_by_uid import LinkByUID

from citrine._rest.resource import ResourceTypeEnum
from citrine.resources.api_error import ApiError
from citrine.resources.dataset import Dataset, DatasetCollection
from citrine.resources.process_spec import ProcessSpec
from citrine.resources.team import Team, TeamCollection, SHARE, READ, WRITE, TeamMember
from citrine.resources.user import User
from tests.utils.factories import UserDataFactory, TeamDataFactory, DatasetDataFactory
from tests.utils.session import FakeSession, FakeCall, FakePaginatedSession


@pytest.fixture
def session() -> FakeSession:
    sess = FakeSession()
    sess._accounts_service_v3 = True
    return sess


@pytest.fixture
def paginated_session() -> FakePaginatedSession:
    return FakePaginatedSession()


@pytest.fixture
def team(session) -> Team:
    team = Team(
        name='Test Team',
        session=session
    )
    team.uid = uuid.UUID('16fd2706-8baf-433b-82eb-8c7fada847da')
    return team


@pytest.fixture
def other_team(session) -> Team:
    team = Team(
        name='Test Team',
        session=session
    )
    team.uid = uuid.uuid4()
    return team


@pytest.fixture
def collection(session) -> TeamCollection:
    return TeamCollection(session)


def test_team_member_string_representation(team):
    user = User.build(UserDataFactory())
    team_member = TeamMember(
        user=user,
        team=team,
        actions=[READ]
    )
    assert team_member.__str__() == '<TeamMember {!r} can {!s} in {!r}>'.format(user.screen_name, team_member.actions, team.name)


def test_string_representation(team):
    assert "<Team 'Test Team'>" == str(team)


def test_team_project_session(team):
    assert team.session == team.projects.session
    assert team.uid == team.projects.team_id


def test_team_registration(collection: TeamCollection, session):
    # Given
    create_time = parse('2019-09-10T00:00:00+00:00')
    team_data = TeamDataFactory(
        name='testing',
        description='A sample team',
        created_at=int(create_time.timestamp() * 1000)  # The lib expects ms since epoch, which is really odd
    )
    user = UserDataFactory()

    session.set_responses(
        {'team': team_data},
        user,
        {'id': user['id'], 'actions': ['READ', 'WRITE', 'SHARE']}
    )

    # When
    created_team = collection.register('testing')

    # Then
    assert 3 == session.num_calls
    expected_call_1 = FakeCall(
        method='POST',
        path='/teams',
        json={
            'name': 'testing',
            'description': '',
            'id': None,
            'created_at': None,
        }
    )
    expected_call_2 = FakeCall(
        method="GET",
        path='/users/me'
    )
    expected_call_3 = FakeCall(method="PUT", path="/teams/{}/users".format(created_team.uid),
                               json={'id': user["id"], 'actions': [READ, WRITE, SHARE]})
    assert expected_call_1 == session.calls[0]
    assert expected_call_2 == session.calls[1]
    assert expected_call_3 == session.calls[2]

    assert 'A sample team' == created_team.description
    assert create_time == created_team.created_at


def test_get_team(collection: TeamCollection, session):
    # Given
    team_data = TeamDataFactory(name='single team')
    session.set_response({'team': team_data})

    # When
    created_team = collection.get(team_data['id'])

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='GET',
        path='/teams/{}'.format(team_data['id']),
    )
    assert expected_call == session.last_call
    assert 'single team' == created_team.name


def test_list_teams(collection, session):
    # Given
    teams_data = TeamDataFactory.create_batch(5)
    session.set_response({'teams': teams_data})

    # When
    teams = list(collection.list())

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(method='GET', path='/teams', params={'per_page': 100, 'page': 1})
    assert expected_call == session.last_call
    assert 5 == len(teams)


def test_list_teams_as_admin(collection, session):
    # Given
    teams_data = TeamDataFactory.create_batch(5)
    session.set_response({"teams": teams_data})

    # When
    teams = list(collection.list(as_admin=True))

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method="GET",
        path="/teams",
        params={"per_page": 100, "page": 1, "as_admin": "true"},
    )
    assert expected_call == session.last_call
    assert 5 == len(teams)


def test_update_team(collection: TeamCollection, team, session):
    team.name = "updated name"
    session.set_response({'team': team.dump()})
    result = collection.update(team)
    assert result.name == team.name


def test_list_members(team, session):
    # Given
    user = UserDataFactory()
    user["actions"] = READ
    user.pop("position")
    session.set_response({'users': [user]})

    # When
    members = team.list_members()

    # Then
    assert 1 == session.num_calls
    expect_call = FakeCall(method='GET', path='/teams/{}/users'.format(team.uid))
    assert expect_call == session.last_call
    assert isinstance(members[0], TeamMember)


def test_me(team, session):
    # Given
    user = UserDataFactory()
    member = user.copy()
    member["actions"] = [READ]
    member.pop("position")
    session.set_responses({**user}, {'user': member})

    # When
    member = team.me()

    # Then
    assert 2 == session.num_calls
    member_call = FakeCall(method='GET', path='/teams/{}/users/{}'.format(team.uid, user["id"]))
    assert member_call == session.last_call
    assert isinstance(member, TeamMember)


def test_update_user_actions(team, session):
    # Given
    user = UserDataFactory()
    session.set_response({'id': user['id'], 'actions': ['READ']})

    # When
    update_user_role_response = team.update_user_action(user_id=User.build(user), actions=[WRITE, SHARE])

    # Then
    assert 1 == session.num_calls
    expect_call = FakeCall(method="PUT", path="/teams/{}/users".format(team.uid),
                           json={'id': user["id"], 'actions': [WRITE, SHARE]})
    assert expect_call == session.last_call
    assert update_user_role_response is True


def test_add_user(team, session):
    # Given
    user = UserDataFactory()
    session.set_response({'id': user["id"], 'actions': ['READ']})

    # When
    add_user_response = team.add_user(User.build(user))

    # Then
    assert 1 == session.num_calls
    expect_call = FakeCall(method="PUT", path='/teams/{}/users'.format(team.uid), json={
        "id": user["id"],
        "actions": ["READ"]
    })
    assert expect_call == session.last_call
    assert add_user_response is True


def test_add_user_with_actions(team, session):
    # Given
    user = UserDataFactory()
    session.set_response({'id': user["id"], 'actions': ['READ', 'WRITE']})

    # When
    add_user_response = team.add_user(user["id"], actions=['READ', 'WRITE'])

    # Then
    assert 1 == session.num_calls
    expect_call = FakeCall(method="PUT", path='/teams/{}/users'.format(team.uid), json={
        "id": user["id"],
        "actions": ["READ", "WRITE"]
    })
    assert expect_call == session.last_call
    assert add_user_response is True


def test_remove_user(team, session):
    # Given
    user = UserDataFactory()
    session.set_response({'ids': [user["id"]]})

    # When
    remove_user_response = team.remove_user(User.build(user))

    # Then
    assert 1 == session.num_calls
    expect_call = FakeCall(
        method="POST",
        path="/teams/{}/users/batch-remove".format(team.uid),
        json={"ids": [user["id"]]}
    )
    assert expect_call == session.last_call
    assert remove_user_response is True


def test_share(team, other_team, session):
    # Given
    dataset = Dataset(name="foo", summary="", description="")
    dataset.uid = str(uuid.uuid4())

    # When
    share_response = team.share(resource=dataset, target_team_id=other_team)

    # Then
    assert 1 == session.num_calls
    expect_call = FakeCall(
        method="POST",
        path="/teams/{}/shared-resources".format(team.uid),
        json={
            "resource_type": "DATASET",
            "resource_id": str(dataset.uid),
            "target_team_id": str(other_team.uid)
        }
    )
    assert expect_call == session.last_call
    assert share_response is True


def test_un_share(team, other_team, session):
    # Given
    dataset = Dataset(name="foo", summary="", description="")
    dataset.uid = str(uuid.uuid4())

    # When
    share_response = team.un_share(resource=dataset, target_team_id=other_team)

    # Then
    assert 1 == session.num_calls
    expect_call = FakeCall(
        method="DELETE",
        path="/teams/{}/shared-resources/{}/{}".format(team.uid, "DATASET", str(dataset.uid)),
        json={
            "target_team_id": str(other_team.uid)
        }
    )
    assert expect_call == session.last_call
    assert share_response is True


@pytest.mark.parametrize("resource_type,method",
    [
        (ResourceTypeEnum.DATASET, "dataset_ids"),
        (ResourceTypeEnum.MODULE, "module_ids"),
        (ResourceTypeEnum.TABLE, "table_ids"),
        (ResourceTypeEnum.TABLE_DEFINITION, "table_definition_ids")
    ])
def test_list_resource_ids(team, session, resource_type, method):
    # Given
    read_response = {'ids': [uuid.uuid4(), uuid.uuid4()]}
    write_response = {'ids': [uuid.uuid4(), uuid.uuid4()]}
    share_response = {'ids': [uuid.uuid4(), uuid.uuid4()]}

    # When
    # This is equivalent to team.dataset_ids, team.module_ids, etc.
    resource_listing = getattr(team, method)
    session.set_response(read_response)
    readable_ids = resource_listing.list_readable()
    session.set_response(write_response)
    writeable_ids = resource_listing.list_writeable()
    session.set_response(share_response)
    shareable_ids = resource_listing.list_shareable()

    with pytest.raises(AttributeError):
        setattr(team, method, [])

    # Then
    assert session.num_calls == 3
    assert session.calls[0] == FakeCall(method='GET',
                                        path=f'/{resource_type.value}/authorized-ids',
                                        params={"domain": f"/teams/{team.uid}", "action": READ})
    assert session.calls[1] == FakeCall(method='GET',
                                        path=f'/{resource_type.value}/authorized-ids',
                                        params={"domain": f"/teams/{team.uid}", "action": WRITE})
    assert session.calls[2] == FakeCall(method='GET',
                                        path=f'/{resource_type.value}/authorized-ids',
                                        params={"domain": f"/teams/{team.uid}", "action": SHARE})
    assert readable_ids == read_response['ids']
    assert writeable_ids == write_response['ids']
    assert shareable_ids == share_response['ids']


def test_analyses_get_team_id(team):
    assert team.uid == team.analyses.team_id

def test_owned_dataset_ids(team):
    # Create a set of datasets in the project
    ids = {uuid.uuid4() for _ in range(5)}
    for d_id in ids:
        dataset = Dataset(name=f"Test Dataset - {d_id}", summary="Test Dataset", description="Test Dataset")
        team.datasets.register(dataset)

    # Set the session response to have the list of dataset IDs
    team.session.set_response({'ids': list(ids)})

    # Fetch the list of UUID owned by the current project
    owned_ids = team.owned_dataset_ids()

    # Let's mock our expected API call so we can compare and ensure that the one made is the same
    expect_call = FakeCall(method='GET',
                           path='/DATASET/authorized-ids',
                           params={'userId': '',
                                   'domain': '/teams/16fd2706-8baf-433b-82eb-8c7fada847da',
                                   'action': 'WRITE'})
    # Compare our calls
    assert expect_call == team.session.last_call
    assert team.session.num_calls == len(ids) + 1
    assert ids == set(owned_ids)

def test_datasets_get_team_id(team):
    assert team.uid == team.datasets.team_id


def test_property_templates_get_team_id(team):
    assert team.uid == team.property_templates.team_id


def test_condition_templates_get_team_id(team):
    assert team.uid == team.condition_templates.team_id


def test_parameter_templates_get_team_id(team):
    assert team.uid == team.parameter_templates.team_id


def test_material_templates_get_team_id(team):
    assert team.uid == team.material_templates.team_id


def test_measurement_templates_get_team_id(team):
    assert team.uid == team.measurement_templates.team_id


def test_process_templates_get_team_id(team):
    assert team.uid == team.process_templates.team_id


def test_process_runs_get_team_id(team):
    assert team.uid == team.process_runs.team_id


def test_measurement_runs_get_team_id(team):
    assert team.uid == team.measurement_runs.team_id


def test_material_runs_get_team_id(team):
    assert team.uid == team.material_runs.team_id


def test_ingredient_runs_get_team_id(team):
    assert team.uid == team.ingredient_runs.team_id


def test_process_specs_get_team_id(team):
    assert team.uid == team.process_specs.team_id


def test_measurement_specs_get_team_id(team):
    assert team.uid == team.measurement_specs.team_id


def test_material_specs_get_team_id(team):
    assert team.uid == team.material_specs.team_id


def test_ingredient_specs_get_team_id(team):
    assert team.uid == team.ingredient_specs.team_id


def test_gemd_resource_get_team_id(team):
    assert team.uid == team.gemd.team_id


def test_team_batch_delete_no_errors(team, session):
    job_resp = {
        'job_id': '1234'
    }

    # Actual response-like data - note there is no 'failures' array within 'output'
    successful_job_resp = {
        'job_type': 'batch_delete',
        'status': 'Success',
        'tasks': [
            {
                "id": "7b6bafd9-f32a-4567-b54c-7ce594edc018", "task_type": "batch_delete",
                "status": "Success", "dependencies": []
             }
            ],
        'output': {}
    }

    session.set_responses(job_resp, successful_job_resp)

    # When
    del_resp = team.gemd_batch_delete([uuid.UUID('16fd2706-8baf-433b-82eb-8c7fada847da')])

    # Then
    assert len(del_resp) == 0

    # When trying with entities
    session.set_responses(job_resp, successful_job_resp)
    entity = ProcessSpec(name="proc spec", uids={'id': '16fd2706-8baf-433b-82eb-8c7fada847da'})
    del_resp = team.gemd_batch_delete([entity])

    # Then
    assert len(del_resp) == 0


def test_team_batch_delete(team, session):
    job_resp = {
        'job_id': '1234'
    }

    failures_escaped_json = json.dumps([
        {
            "id": {
                'scope': 'somescope',
                'id': 'abcd-1234'
            },
            'cause': {
                "code": 400,
                "message": "",
                "validation_errors": [
                    {
                        "failure_message": "fail msg",
                        "failure_id": "identifier.coreid.missing"
                    }
                ]
            }
        }
    ])

    failed_job_resp = {
        'job_type': 'batch_delete',
        'status': 'Success',
        'tasks': [],
        'output': {
            'failures': failures_escaped_json
        }
    }

    session.set_responses(job_resp, failed_job_resp, job_resp, failed_job_resp)

    # When
    del_resp = team.gemd_batch_delete([uuid.UUID('16fd2706-8baf-433b-82eb-8c7fada847da')])

    # Then
    assert 2 == session.num_calls

    assert len(del_resp) == 1
    first_failure = del_resp[0]

    expected_api_error = ApiError.build({
        "code": "400",
        "message": "",
        "validation_errors": [{"failure_message": "fail msg", "failure_id": "identifier.coreid.missing"}]
    })

    assert first_failure[0] == LinkByUID('somescope', 'abcd-1234')
    assert first_failure[1].dump() == expected_api_error.dump()

    # And again with tuples of (scope, id)
    del_resp = team.gemd_batch_delete([LinkByUID('id', '16fd2706-8baf-433b-82eb-8c7fada847da')])
    assert len(del_resp) == 1
    first_failure = del_resp[0]

    assert first_failure[0] == LinkByUID('somescope', 'abcd-1234')
    assert first_failure[1].dump() == expected_api_error.dump()


def test_batch_delete_bad_input(team):
    with pytest.raises(TypeError):
        team.gemd_batch_delete([True])
