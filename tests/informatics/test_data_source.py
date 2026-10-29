"""Tests for citrine.informatics.descriptors."""

import uuid

import pytest

from citrine.informatics.data_sources import DataSource, SnapshotDataSource


@pytest.fixture(
    params=[
        SnapshotDataSource(snapshot_id=uuid.uuid4()),
    ]
)
def data_source(request):
    return request.param


def test_deser_from_parent(data_source):
    # Serialize and deserialize the descriptors, making sure they are round-trip serializable
    data = data_source.dump()
    data_source_deserialized = DataSource.build(data)
    assert data_source == data_source_deserialized


def test_invalid_eq(data_source):
    other = None
    assert not data_source == other


def test_invalid_deser():
    with pytest.raises(ValueError):
        DataSource.build({})

    with pytest.raises(ValueError):
        DataSource.build({"type": "foo"})


def test_data_source_id(data_source):
    assert data_source == DataSource.from_data_source_id(data_source.to_data_source_id())


def test_invalid_data_source_id():
    with pytest.raises(ValueError):
        DataSource.from_data_source_id(f"Undefined::{uuid.uuid4()}")
