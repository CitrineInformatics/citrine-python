"""Tests for citrine.informatics.descriptors."""

import uuid

import pytest

from citrine.informatics.data_sources import (
    DataSource,
    CSVDataSource,
    ExperimentDataSourceRef,
    GemTableDataSource,
    SnapshotDataSource,
)
from citrine.informatics.descriptors import RealDescriptor
from citrine.resources.file_link import FileLink
from citrine.resources.gemtables import GemTable

from tests.utils.factories import GemTableDataFactory


@pytest.fixture(
    params=[
        GemTableDataSource(table_id=uuid.uuid4(), table_version=1),
        GemTableDataSource(table_id=uuid.uuid4(), table_version="2"),
        ExperimentDataSourceRef(datasource_id=uuid.uuid4()),
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
    assert data_source == DataSource.from_data_source_id(
        data_source.to_data_source_id()
    )


def test_from_gem_table():
    table = GemTable.build(GemTableDataFactory())
    data_source = GemTableDataSource.from_gemtable(table)
    assert data_source.table_id == table.uid
    assert data_source.table_version == table.version


def test_invalid_data_source_id():
    with pytest.raises(ValueError):
        DataSource.from_data_source_id(f"Undefined::{uuid.uuid4()}")


def test_deser_from_parent_deprecated():
    with pytest.deprecated_call():
        data_source = CSVDataSource(
            file_link=FileLink("foo.spam", "http://example.com"),
            column_definitions={
                "spam": RealDescriptor("eggs", lower_bound=0, upper_bound=1.0, units="")
            },
            identifiers=["identifier"],
        )

    # Serialize and deserialize the descriptors, making sure they are round-trip serializable
    data = data_source.dump()
    data_source_deserialized = DataSource.build(data)
    assert data_source == data_source_deserialized


def test_data_source_id_deprecated():
    with pytest.deprecated_call():
        data_source = CSVDataSource(
            file_link=FileLink("foo.spam", "http://example.com"),
            column_definitions={
                "spam": RealDescriptor("eggs", lower_bound=0, upper_bound=1.0, units="")
            },
            identifiers=["identifier"],
        )

    # TODO: There's no obvious way to recover the column_definitions & identifiers from the ID
    with pytest.deprecated_call():
        with pytest.warns(UserWarning):
            transformed = DataSource.from_data_source_id(
                data_source.to_data_source_id()
            )
    assert transformed.file_link == data_source.file_link
