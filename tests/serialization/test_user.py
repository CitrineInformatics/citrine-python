"""Tests of the Project schema."""
import pytest
from uuid import uuid4
from citrine.resources.user import User


@pytest.fixture
def valid_data():
    """Return valid data used for these tests."""
    return dict(
        id=str(uuid4()),
        screenName='bob',
        position='the builder',
        email='bob@thebuilder.com',
        isAdmin=True
    )


def test_simple_deserialization(valid_data):
    """Ensure a deserialized User looks sane."""
    user: User = User.build(valid_data)
    assert user.screen_name == 'bob'
    assert user.position == 'the builder'
    assert user.email == 'bob@thebuilder.com'
    assert user.is_admin


def test_serialization(valid_data):
    """Ensure a serialized User looks sane."""
    user: User = User.build(valid_data)
    serialized = user.dump()
    assert serialized == valid_data
