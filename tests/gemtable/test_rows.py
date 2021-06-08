"""Tests for citrine.informatics.rows."""
import pytest

from citrine.gemtables.rows import MaterialRunByTemplate, Row
from gemd.entity.link_by_uid import LinkByUID


@pytest.fixture(params=[
    MaterialRunByTemplate(templates=[
        LinkByUID(scope="templates", id="density"), LinkByUID(scope="templates", id="ingredients")
    ]),
])
def row(request):
    return request.param


def test_deser_from_parent(row):
    # Serialize and deserialize the rows, making sure they are round-trip serializable
    row_data = row.dump()
    row_deserialized = Row.build(row_data)
    assert row == row_deserialized


def test_invalid_eq(row):
    other = None
    assert not row == other


def test_invalid_deser():
    with pytest.raises(ValueError):
        Row.build({})

    with pytest.raises(ValueError):
        Row.build({"type": "foo"})
