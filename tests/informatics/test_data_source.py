"""Tests for citrine.informatics.descriptors."""
import uuid

import pytest

from citrine.informatics.data_sources import (
    DataSource, ExperimentDataSourceRef, GemTableDataSource, SnapshotDataSource
)
from citrine.informatics.descriptors import RealDescriptor
from citrine.resources.file_link import FileLink
from citrine.resources.gemtables import GemTable

from tests.utils.factories import GemTableDataFactory

@pytest.fixture(params=[
    GemTableDataSource(table_id=uuid.uuid4(), table_version=1),
    GemTableDataSource(table_id=uuid.uuid4(), table_version="2"),
    SnapshotDataSource(snapshot_id=uuid.uuid4())
])
def data_source(request):
    return request.param

@pytest.fixture
def deprecated_data_source():
    with pytest.deprecated_call():
        return ExperimentDataSourceRef(datasource_id=uuid.uuid4())


def test_deser_from_parent(data_source):
    # Serialize and deserialize the descriptors, making sure they are round-trip serializable
    data = data_source.dump()
    data_source_deserialized = DataSource.build(data)
    assert data_source == data_source_deserialized


def test_deser_from_parent_deprecated(deprecated_data_source):
    # Serialize and deserialize the descriptors, making sure they are round-trip serializable
    data = deprecated_data_source.dump()
    data_source_deserialized = DataSource.build(data)
    assert deprecated_data_source == data_source_deserialized


def test_invalid_eq(data_source):
    other = None
    assert not data_source == other


def test_invalid_eq(deprecated_data_source):
    other = None
    assert not deprecated_data_source == other


def test_invalid_deser():
    with pytest.raises(ValueError):
        DataSource.build({})

    with pytest.raises(ValueError):
        DataSource.build({"type": "foo"})


def test_deprecated_data_source_id(deprecated_data_source):
    with pytest.deprecated_call():
        assert deprecated_data_source == DataSource.from_data_source_id(deprecated_data_source.to_data_source_id())

def test_data_source_id(data_source):
    assert data_source == DataSource.from_data_source_id(data_source.to_data_source_id())

def test_from_gem_table():
    table = GemTable.build(GemTableDataFactory())
    data_source = GemTableDataSource.from_gemtable(table)
    assert data_source.table_id == table.uid
    assert data_source.table_version == table.version

def test_invalid_data_source_id():
    with pytest.raises(ValueError):
        DataSource.from_data_source_id(f"Undefined::{uuid.uuid4()}")
