"""Tests for citrine.informatics.variables."""
import pytest

from citrine.ara.variables import Variable, RootInfo, AttributeByTemplate
from taurus.entity.link_by_uid import LinkByUID


@pytest.fixture(params=[
    RootInfo(name="root name", headers=["Root", "Name"], field="name"),
    AttributeByTemplate(name="density", headers=["density"], template=LinkByUID(scope="templates", id="density"))
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


def test_invalid_deser():
    with pytest.raises(ValueError):
        Variable.build({})

    with pytest.raises(ValueError):
        Variable.build({"type": "foo"})
