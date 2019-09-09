"""Tests for citrine.informatics.descriptors."""
import pytest

from citrine.informatics.descriptors import RealDescriptor, Descriptor, InorganicDescriptor, CategoricalDescriptor


@pytest.fixture(params=[
    RealDescriptor('alpha', 0, 100),
    InorganicDescriptor('formula'),
    CategoricalDescriptor("my categorical", ["a", "b"]),
    CategoricalDescriptor("categorical", ["*"])
])
def descriptor(request):
    return request.param


def test_deser_from_parent(descriptor):
    # Serialize and deserialize the descriptors, making sure they are round-trip serializable
    descriptor_data = descriptor.dump()
    descriptor_deserialized = Descriptor.build(descriptor_data)
    assert descriptor == descriptor_deserialized
