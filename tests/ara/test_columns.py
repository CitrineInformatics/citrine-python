"""Tests for citrine.informatics.columns."""
import pytest

from citrine.ara.columns import MeanColumn, IdentityColumn, Column, StdDevColumn, QuantileColumn, \
    OriginalUnitsColumn, MostLikelyProbabilityColumn, MostLikelyCategoryColumn


@pytest.fixture(params=[
    IdentityColumn(data_source="root name"),
    MeanColumn(data_source="density", target_units="g/cm^3"),
    StdDevColumn(data_source="density", target_units="g/cm^3"),
    QuantileColumn(data_source="density", quantile=0.95),
    OriginalUnitsColumn(data_source="density"),
    MostLikelyCategoryColumn(data_source="color"),
    MostLikelyProbabilityColumn(data_source="color"),
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


def test_invalid_deser():
    with pytest.raises(ValueError):
        Column.build({})

    with pytest.raises(ValueError):
        Column.build({"type": "foo"})
