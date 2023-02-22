from uuid import UUID

import pytest

from citrine.resources.user import User, UserCollection
from tests.utils.factories import UserDataFactory
from tests.utils.session import FakeSession, FakeCall


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def user() -> User:
    user = User(
        screen_name='Test User',
        email="test@user.io",
        position="QA",
        is_admin=False
    )
    user.uid = UUID('16fd2706-8baf-433b-82eb-8c7fada847da')
    return user


@pytest.fixture
def collection(session) -> UserCollection:
    return UserCollection(session)


def test_user_str_representation():
    user = User(
        screen_name='joe',
        email='joe@somewhere.com',
        position='President',
        is_admin=False
    )
    assert "<User 'joe'>" == str(user)


def test_user_collection_creation():
    session = FakeSession()

    assert session == UserCollection(session).session


def test_user_registration(collection, session):
    # given
    user = UserDataFactory()

    session.set_response({'user': user})

    # When
    created_user = collection.register(
        screen_name=user["screen_name"],
        email=user["email"],
        position=user["position"],
        is_admin=user["is_admin"]
    )

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='POST',
        path='/users',
        json={
            'screen_name': user["screen_name"],
            'position': user["position"],
            'email': user["email"],
            'is_admin': user["is_admin"],
        }
    )

    assert expected_call.json['screen_name'] == created_user.screen_name
    assert expected_call.json['email'] == created_user.email
    assert expected_call.json['position'] == created_user.position
    assert expected_call.json['is_admin'] == created_user.is_admin


def test_list_users(collection, session):
    # Given
    user_data = UserDataFactory.create_batch(5)
    session.set_response({'users': user_data})

    # When
    users = list(collection.list())

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='GET',
        path='/users',
        params={'per_page': 100, 'page': 1}
    )

    assert expected_call == session.last_call
    assert len(users) == 5


def test_get_users(collection, session):
    # Given
    uid = '151199ec-e9aa-49a1-ac8e-da722aaf74c4'

    # When
    with pytest.raises(KeyError):
        collection.get(uid)


def test_delete_user(collection, session):
    # Given
    user = UserDataFactory()

    # When
    collection.delete(user['id'])

    session.set_response({'message': 'User was deleted'})
    expected_call = FakeCall(
        method="DELETE",
        path='/users/{}'.format(user["id"]),
    )

    assert 1 == session.num_calls
    assert expected_call == session.last_call


def test_get_me(collection, session):
    # Given
    user = UserDataFactory()
    session.set_response(user)

    # When
    current_user = collection.me()

    # Then
    expected_call = FakeCall(
        method="GET",
        path='/users/me'
    )
    assert 1 == session.num_calls
    assert expected_call == session.last_call


def test_user_get_not_implemented(user):
    with pytest.raises(NotImplementedError):
        user.get()
