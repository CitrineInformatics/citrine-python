"""Tests for citrine.informatics.descriptors."""
import uuid

import pytest

from citrine.informatics.data_sources import DataSource, CSVDataSource, ExperimentDataSourceRef, GemTableDataSource
from citrine.informatics.descriptors import RealDescriptor, FormulationDescriptor
from citrine.resources.file_link import FileLink


@pytest.fixture(params=[
    CSVDataSource(file_link=FileLink("foo.spam", "http://example.com"),
                  column_definitions={"spam": RealDescriptor("eggs", lower_bound=0, upper_bound=1.0, units="")},
                  identifiers=["identifier"]),
    GemTableDataSource(table_id=uuid.uuid4(), table_version=1),
    GemTableDataSource(table_id=uuid.uuid4(), table_version="2"),
    GemTableDataSource(table_id=uuid.uuid4(), table_version="2"),
    ExperimentDataSourceRef(datasource_id=uuid.uuid4())
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


def test_deprecated_formulation_option():
    with pytest.warns(DeprecationWarning):
        GemTableDataSource(
            table_id=uuid.uuid4(),
            table_version=1,
            formulation_descriptor=FormulationDescriptor.hierarchical()
        )
