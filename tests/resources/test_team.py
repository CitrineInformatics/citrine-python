import uuid
from logging import getLogger

import pytest
from dateutil.parser import parse

from citrine._rest.resource import ResourceTypeEnum
from citrine.resources.dataset import Dataset
from citrine.resources.team import Team, TeamCollection, SHARE, READ, WRITE, TeamMember
from tests.utils.factories import UserDataFactory, TeamDataFactory
from tests.utils.session import FakeSession, FakeCall, FakePaginatedSession

logger = getLogger(__name__)


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
def collection(session) -> TeamCollection:
    return TeamCollection(session)


def test_string_representation(team):
    assert "<Team 'Test Team'>" == str(team)


def test_team_registration(collection: TeamCollection, session):
    # Given
    create_time = parse('2019-09-10T00:00:00+00:00')
    team_data = TeamDataFactory(
        name='testing',
        description='A sample team',
        created_at=int(create_time.timestamp() * 1000)  # The lib expects ms since epoch, which is really odd
    )
    session.set_response({'team': team_data})

    # When
    created_team = collection.register('testing')

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='POST',
        path='/teams',
        json={
            'name': 'testing',
            'description': '',
            'id': None,
            'created_at': None,
        }
    )
    assert expected_call == session.last_call

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
    expected_call = FakeCall(method='GET', path='/teams', params={'per_page': 100})
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
    session.set_response({'users': [user]})

    # When
    members = team.list_members()

    # Then
    assert 1 == session.num_calls
    expect_call = FakeCall(method='GET', path='/teams/{}/users'.format(team.uid))
    assert expect_call == session.last_call
    assert isinstance(members[0], TeamMember)


def test_update_user_actions(team, session):
    # Given
    user = UserDataFactory()
    session.set_response({'id': user['id'], 'actions': ['READ']})

    # When
    update_user_role_response = team.update_user_action(user_id=user["id"], actions=[WRITE, SHARE])

    # Then
    assert 1 == session.num_calls
    expect_call = FakeCall(method="PUT", path="/teams/{}/users".format(team.uid),
                           json={'id': user["id"], 'actions': [WRITE, SHARE]})
    assert expect_call == session.last_call
    assert update_user_role_response is True


def test_add_user(team, session):
    # Given
    user = UserDataFactory()
    session.set_response({'id': user["id"], 'actions': 'READ'})

    # When
    add_user_response = team.add_user(user["id"])

    # Then
    assert 1 == session.num_calls
    expect_call = FakeCall(method="PUT", path='/teams/{}/users'.format(team.uid), json={
        "id": user["id"],
        "actions": ["READ"]
    })
    assert expect_call == session.last_call
    assert add_user_response is True


def test_remove_user(team, session):
    # Given
    user = UserDataFactory()
    session.set_response({'ids': [user["id"]]})

    # When
    remove_user_response = team.remove_user(user["id"])

    # Then
    assert 1 == session.num_calls
    expect_call = FakeCall(
        method="POST",
        path="/teams/{}/users/batch-remove".format(team.uid),
        json={"ids": [user["id"]]}
    )
    assert expect_call == session.last_call
    assert remove_user_response is True


def test_share(team, session):
    # Given
    target_team_id = uuid.uuid4()
    dataset = Dataset(name="foo", summary="", description="")
    dataset.uid = str(uuid.uuid4())

    # When
    share_response = team.share(resource=dataset, target_team_id=target_team_id)

    # Then
    assert 1 == session.num_calls
    expect_call = FakeCall(
        method="POST",
        path="/teams/{}/shared-resources".format(team.uid),
        json={
            "resource_type": "DATASET",
            "resource_id": str(dataset.uid),
            "target_team_id": str(target_team_id)
        }
    )
    assert expect_call == session.last_call
    assert share_response is True
