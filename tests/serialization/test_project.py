"""Tests of the Project schema."""
import pytest
from uuid import uuid4, UUID
from citrine.resources.project import Project
import arrow


@pytest.fixture
def valid_data():
    """Return valid data used for these tests."""
    return dict(
        id=str(uuid4()),
        created_at=1559933807392,
        name='my project',
        description='a good project',
        status='in-progress'
    )


def test_simple_deserialization(valid_data):
    """Ensure that a deserialized Project looks sane."""
    project: Project = Project.build(valid_data)
    assert project.uid == UUID(valid_data['id'])
    assert project.created_at == arrow.get(valid_data['created_at'] / 1000).datetime
    assert project.name == 'my project'
    assert project.status == 'in-progress'


def test_serialization(valid_data):
    """Ensure that a serialized Project looks sane."""
    project: Project = Project.build(valid_data)
    serialized = project.dump()
    assert serialized == valid_data
