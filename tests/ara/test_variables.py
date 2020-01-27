"""Tests for citrine.informatics.variables."""
import pytest

from citrine.ara.variables import *
from taurus.entity.link_by_uid import LinkByUID


@pytest.fixture(params=[
    RootInfo(name="root name", headers=["Root", "Name"], field="name"),
    AttributeByTemplate(name="density", headers=["density"], template=LinkByUID(scope="templates", id="density")),
    AttributeByTemplateAfterProcessTemplate(name="density", headers=["density"], attributeTemplate=LinkByUID(scope="template", id="density"), processTemplate=LinkByUID(scope="template", id="process1")),
    AttributeByTemplateAndObjectTemplate(name="density", headers=["density"], attributeTemplate=LinkByUID(scope="template", id="density"), objectTemplate=LinkByUID(scope="template", id="object")),
    IngredientIdentifierByProcessTemplateAndName(name="ingredient id", headers=["density"], processTemplate=LinkByUID(scope="template", id="process"), ingredientName="ingredient", scope="scope"),
    IngredientLabelByProcessAndName(name="ingredient label", headers=["label"], processTemplate=LinkByUID(scope="template", id="process"), ingredientName="ingredient", label="label"),
    IngredientQuantityByProcessAndName(name="ingredient quantity dimension", headers=["quantity"], processTemplate=LinkByUID(scope="template", id="process"), ingredientName="ingredient", quantityDimension=IngredientQuantityDimension.absolute),
    RootIdentifier(name="root id", headers=["id"], scope="scope")
])
def variable(request):
    return request.param


def test_deser_from_parent(variable):
    # Serialize and deserialize the variables, making sure they are round-trip serializable
    variable_data = variable.dump()
    variable_deserialized = Variable.build(variable_data)
    for attr in variable._attrs():
        variable_attr = getattr(variable, attr)
        variable_deser_attr = getattr(variable_deserialized, attr)
        assert variable_attr == variable_deser_attr
    assert variable == variable_deserialized


def test_invalid_eq(variable):
    other = None
    assert not variable == other


def test_invalid_deser():
    with pytest.raises(ValueError):
        Variable.build({})

    with pytest.raises(ValueError):
        Variable.build({"type": "foo"})
