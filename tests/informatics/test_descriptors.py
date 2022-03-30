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
    FormulationDescriptor("formulation")
])
def descriptor(request):
    return request.param


def test_deser_from_parent(descriptor):
    # Serialize and deserialize the descriptors, making sure they are round-trip serializable
    descriptor_data = descriptor.dump()
    descriptor_deserialized = Descriptor.build(descriptor_data)
    assert descriptor == descriptor_deserialized


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
