from citrine.resources.user import User, UserCollection
from tests.utils.session import FakeSession


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
