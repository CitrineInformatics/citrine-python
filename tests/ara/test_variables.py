"""Tests for citrine.informatics.variables."""
import pytest

from citrine.ara.variables import Variable, RootInfo


@pytest.fixture(params=[
    RootInfo("root name", ["Root", "Name"], "name"),
])
def variable(request):
    return request.param


def test_deser_from_parent(variable):
    # Serialize and deserialize the variables, making sure they are round-trip serializable
    variable_data = variable.dump()
    variable_deserialized = Variable.build(variable_data)
    assert variable == variable_deserialized


def test_invalid_eq(variable):
    other = None
    assert not variable == other
