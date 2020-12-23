"""Tests for citrine.informatics.descriptors."""
import json

import pytest

from citrine.informatics.descriptors import *


@pytest.fixture(params=[
    RealDescriptor('alpha', 0, 100),
    ChemicalFormulaDescriptor('formula'),
    MolecularStructureDescriptor("organic"),
    CategoricalDescriptor("my categorical", ["a", "b"]),
    CategoricalDescriptor("categorical", ["*"]),
    FormulationDescriptor("formulation")
])
def descriptor(request):
    return request.param


def test_deser_from_parent(descriptor):
    # Serialize and deserialize the descriptors, making sure they are round-trip serializable
    descriptor_data = descriptor.dump()
    descriptor_deserialized = Descriptor.build(descriptor_data)
    assert descriptor == descriptor_deserialized


def test_buggy_deserialization():
    """Should be able to deserialize a descriptor with type key 'category'.
    THIS IS TEMPORARY, TO BE REMOVED AS SOON AS PLA-4036 IS FIXED.
    """
    buggy_data = dict(
        descriptor_key='key',
        lower_bound=0,
        upper_bound=1,
        units="",
        category='Real'
    )
    Descriptor.build(buggy_data)


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
        CategoricalDescriptor("my categorical", ["a", "b", 1])
    with pytest.raises(TypeError):
        CategoricalDescriptor("my categorical", ["a", "b", None])


def test_to_json(descriptor):
    """Make sure we can dump the descriptors to json"""
    json_str = json.dumps(descriptor.dump())
    desc = Descriptor.build(json.loads(json_str))
    assert desc == descriptor

