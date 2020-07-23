"""Tests for citrine.informatics.descriptors."""
import uuid

import pytest

from citrine.informatics.data_sources import DataSource, CSVDataSource, GemTableDataSource
from citrine.informatics.descriptors import RealDescriptor
from citrine.resources.file_link import FileLink


@pytest.fixture(params=[
    CSVDataSource(FileLink("foo.spam", "http://example.com"), {"spam": RealDescriptor("eggs", lower_bound=0, upper_bound=1.0)}, ["identifier"]),
    GemTableDataSource(uuid.uuid4(), 1),
    GemTableDataSource(uuid.uuid4(), "2"),
])
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
