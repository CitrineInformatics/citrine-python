import uuid
from logging import getLogger

import pytest
from dateutil.parser import parse

from citrine.resources.project import ProjectCollection
from citrine.resources.project_roles import MEMBER, WRITE
from citrine.resources.team import Team, TeamCollection
from tests.utils.factories import UserDataFactory, TeamDataFactory
from tests.utils.session import FakeSession, FakeCall, FakePaginatedSession

logger = getLogger(__name__)


@pytest.fixture
def session_v1() -> FakeSession:
    return FakeSession()


@pytest.fixture
def session() -> FakeSession:
    sess = FakeSession()
    sess._accounts_service_v3 = True
    return sess


@pytest.fixture
def paginated_session() -> FakePaginatedSession:
    return FakePaginatedSession()


@pytest.fixture
def paginated_collection(paginated_session) -> ProjectCollection:
    return ProjectCollection(
        session=paginated_session
    )


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
            'description': None,
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
    collection.update(team)


def test_list_members(team, session):
    # Given
    user = UserDataFactory()
    user["role"] = MEMBER
    session.set_response({'users': [user]})

    # When
    with pytest.raises(NotImplementedError):
        members = team.list_members()

    # Then
    # assert 1 == session.num_calls
    # expect_call = FakeCall(method='GET', path='/teams/{}/users'.format(team.uid))
    # assert expect_call == session.last_call
    # assert isinstance(members[0], ProjectMember)
#     TODO assert something else


def test_update_user_actions(team, session):
    # Given
    user = UserDataFactory()
    session.set_response({'actions': ['READ']})

    # When
    with pytest.raises(NotImplementedError):
        update_user_role_response = team.update_user_action(user_id=user["id"], actions=[WRITE])

    # Then
    # assert 1 == session.num_calls
    # expect_call = FakeCall(method="POST", path="/teams/{}/users".format(team.uid),
    #                        json={'id': user["id"], 'actions': [WRITE]})
    # assert expect_call == session.last_call
    # assert update_user_role_response is True


def test_add_user(team, session):
    # Given
    user = UserDataFactory()
    session.set_response({'actions': [], 'role': 'MEMBER'})

    # When
    with pytest.raises(NotImplementedError):
        add_user_response = team.add_user(user["id"])

    # Then
    # assert 1 == session.num_calls
    # expect_call = FakeCall(method="POST", path='/projects/{}/users/{}'.format(team.uid, user["id"]), json={
    #     "role": "MEMBER",
    #     "actions": []
    # })
    # assert expect_call == session.last_call
    # assert add_user_response is True


def test_remove_user(team, session):
    # Given
    user = UserDataFactory()

    # When
    with pytest.raises(NotImplementedError):
        remove_user_response = team.remove_user(user["id"])

    # Then
    # assert 1 == session.num_calls
    # expect_call = FakeCall(
    #     method="DELETE",
    #     path="/projects/{}/users/{}".format(team.uid, user["id"])
    # )
    # assert expect_call == session.last_call
    # assert remove_user_response is True


def test_share(team, session):
    # Given
    user = UserDataFactory()

    # When
    with pytest.raises(NotImplementedError):
        share_response = team.share(user["id"], uuid.uuid4())

    # Then
    # assert 1 == session.num_calls
    # expect_call = FakeCall(
    #     method="DELETE",
    #     path="/projects/{}/users/{}".format(team.uid, user["id"])
    # )
    # assert expect_call == session.last_call
    # assert remove_user_response is True
