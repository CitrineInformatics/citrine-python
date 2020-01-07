"""Tests for citrine.informatics.columns."""
import pytest

from citrine.ara.columns import RealMeanColumn, IdentityColumn, Column


@pytest.fixture(params=[
    RealMeanColumn("density", "g/cm^3"),
    IdentityColumn("root name")
])
def column(request):
    return request.param


def test_deser_from_parent(column):
    # Serialize and deserialize the columns, making sure they are round-trip serializable
    column_data = column.dump()
    column_deserialized = Column.build(column_data)
    assert column == column_deserialized


def test_invalid_eq(column):
    other = None
    assert not column == other
