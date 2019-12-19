"""Tests of the Dataset schema."""
import pytest
from uuid import uuid4, UUID
from citrine.resources.dataset import Dataset
import arrow


@pytest.fixture
def valid_data():
    """Return valid data used for these tests."""
    return dict(
        id=str(uuid4()),
        name='Dataset 1',
        summary='The first dataset',
        description='A dummy dataset for performing unit tests',
        deleted=True,
        created_by=None,
        updated_by=None,
        deleted_by=None,
        create_time=1559933807392,
        update_time=None,
        delete_time=None,
        public=False
    )


def test_simple_deserialization(valid_data):
    """Ensure that a deserialized Dataset looks sane."""
    dataset: Dataset = Dataset.build(valid_data)
    assert dataset.uid == UUID(valid_data['id'])
    assert dataset.name == 'Dataset 1'
    assert dataset.summary == 'The first dataset'
    assert dataset.description == 'A dummy dataset for performing unit tests'
    assert dataset.deleted
    assert dataset.create_time == arrow.get(valid_data['create_time'] / 1000).datetime


def test_serialization(valid_data):
    """Ensure that a serialized Dataset looks sane."""
    dataset: Dataset = Dataset.build(valid_data)
    serialized = dataset.dump()
    assert serialized == valid_data
