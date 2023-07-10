"""Tests for citrine.informatics.descriptors."""
import json

import pytest

from citrine.informatics.descriptors import *


@pytest.fixture(params=[
    RealDescriptor('alpha', lower_bound=0, upper_bound=100, units=""),
    IntegerDescriptor('count', lower_bound=0, upper_bound=100),
    ChemicalFormulaDescriptor('formula'),
    MolecularStructureDescriptor("organic"),
    CategoricalDescriptor("my categorical", categories=["a", "b"]),
    CategoricalDescriptor("categorical", categories=["*"]),
    FormulationDescriptor.hierarchical()
])
def descriptor(request):
    return request.param


def test_deser_from_parent(descriptor):
    # Serialize and deserialize the descriptors, making sure they are round-trip serializable
    descriptor_data = descriptor.dump()
    descriptor_deserialized = Descriptor.build(descriptor_data)
    assert descriptor == descriptor_deserialized


def test_equals(descriptor):

    assert descriptor._equals(descriptor, descriptor.__dict__.keys())

    # attributes missing from the descriptor should raise an exception
    with pytest.raises(AttributeError):
        descriptor._equals(None, ["missing_attr"])

    # attributes missing from the 'other' instance should return False
    assert not descriptor._equals(None, ["key"])


def test_invalid_eq(descriptor):
    other = None
    assert not descriptor == other


def test_string_rep(descriptor):
    """String representation of descriptor should contain the descriptor key."""
    assert str(descriptor).__contains__(descriptor.key)
    assert repr(descriptor).__contains__(descriptor.key)


def test_categorical_descriptor_categories_types():
    """Categories in a categorical descriptor should be of type str, and other types should raise TypeError."""
    with pytest.raises(TypeError):
        CategoricalDescriptor("my categorical", categories=["a", "b", 1])
    with pytest.raises(TypeError):
        CategoricalDescriptor("my categorical", categories=["a", "b", None])


def test_to_json(descriptor):
    """Make sure we can dump the descriptors to json"""
    json_str = json.dumps(descriptor.dump())
    desc = Descriptor.build(json.loads(json_str))
    assert desc == descriptor


def test_formulation_from_string_key():
    descriptor = FormulationDescriptor(FormulationKey.HIERARCHICAL.value)
    assert descriptor.key == FormulationKey.HIERARCHICAL.value


def test_integer_units_deprecation():
    descriptor = IntegerDescriptor("integer", lower_bound=5, upper_bound=10)
    with pytest.deprecated_call():
        assert descriptor.units == "dimensionless"
