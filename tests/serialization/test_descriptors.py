"""Tests for citrine.informatics.descriptors serialization."""
import pytest

from citrine.informatics.descriptors import RealDescriptor, Descriptor


@pytest.fixture
def valid_data():
    """Produce valid descriptor data."""
    return dict(
        type='Real',
        descriptor_key='alpha',
        units='',
        lower_bound=5.0,
        upper_bound=10.0,
    )


def test_simple_deserialization(valid_data):
    """Ensure a deserialized RealDescriptor looks sane."""
    descriptor = RealDescriptor.build(valid_data)
    assert descriptor.key == 'alpha'
    assert descriptor.units == ''
    assert descriptor.lower_bound == 5.0
    assert descriptor.upper_bound == 10.0


def test_polymorphic_deserialization(valid_data):
    """Ensure a polymorphically deserialized RealDescriptor looks sane."""
    descriptor: RealDescriptor = Descriptor.build(valid_data)
    assert descriptor.key == 'alpha'
    assert descriptor.units == ''
    assert descriptor.lower_bound == 5.0
    assert descriptor.upper_bound == 10.0


def test_serialization(valid_data):
    """Ensure a serialized RealDescriptor looks sane."""
    descriptor = RealDescriptor.build(valid_data)
    serialized = descriptor.dump()
    assert serialized == valid_data
