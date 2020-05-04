"""Tests for citrine.informatics.descriptors."""
import pytest

from citrine.informatics.descriptors import *
from citrine.informatics.descriptors import InorganicDescriptor


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


def test_invalid_eq(descriptor):
    other = None
    assert not descriptor == other


def test_inorganic_deprecated():
    # InorganicDescriptor is still callable but creates a ChemicalFormulaDescriptor
    old_descriptor = InorganicDescriptor("formula")
    assert isinstance(old_descriptor, ChemicalFormulaDescriptor)
