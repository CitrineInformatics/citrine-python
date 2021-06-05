"""Tests for citrine.informatics.dimensions serialization."""
import uuid

import pytest

from citrine.informatics.descriptors import RealDescriptor, CategoricalDescriptor
from citrine.informatics.dimensions import Dimension, ContinuousDimension, EnumeratedDimension


@pytest.fixture
def valid_continuous_data():
    """Produce valid continuous dimension data."""
    return dict(
        type='ContinuousDimension',
        descriptor=dict(
            type='Real',
            descriptor_key='alpha',
            units='',
            lower_bound=5.0,
            upper_bound=10.0,
        ),
        lower_bound=6.0,
        upper_bound=7.0
    )


@pytest.fixture
def valid_enumerated_data():
    """Produce valid enumerated dimension data."""
    return dict(
        type='EnumeratedDimension',
        descriptor=dict(
            type='Categorical',
            descriptor_key='color',
            descriptor_values=['blue', 'green', 'red'],
        ),
        list=['red']
    )


def test_simple_continuous_deserialization(valid_continuous_data):
    """Ensure that a deserialized ContinuousDimension looks sane."""
    dimension = ContinuousDimension.build(valid_continuous_data)
    assert type(dimension) == ContinuousDimension
    assert dimension.lower_bound == 6.0
    assert dimension.upper_bound == 7.0
    assert type(dimension.descriptor) == RealDescriptor


def test_polymorphic_continuous_deserialization(valid_continuous_data):
    """Ensure that a polymorphically deserialized ContinuousDimension looks sane."""
    dimension: ContinuousDimension = Dimension.build(valid_continuous_data)
    assert type(dimension) == ContinuousDimension
    assert dimension.lower_bound == 6.0
    assert dimension.upper_bound == 7.0
    assert type(dimension.descriptor) == RealDescriptor


def test_continuous_serialization(valid_continuous_data):
    """Ensure that a serialized ContinuousDimension looks sane."""
    dimension = ContinuousDimension.build(valid_continuous_data)
    serialized = dimension.dump()
    assert serialized == valid_continuous_data


def test_simple_enumerated_deserialization(valid_enumerated_data):
    """Ensure that a deserialized EnumeratedDimension looks sane."""
    dimension: EnumeratedDimension = EnumeratedDimension.build(valid_enumerated_data)
    assert type(dimension) == EnumeratedDimension
    assert dimension.values == ['red']
    assert type(dimension.descriptor) == CategoricalDescriptor


def test_polymorphic_enumerated_deserialization(valid_enumerated_data):
    """Ensure that a polymorphically deserialized EnumeratedDimension looks sane."""
    dimension: EnumeratedDimension = Dimension.build(valid_enumerated_data)
    assert type(dimension) == EnumeratedDimension
    assert dimension.values == ['red']
    assert type(dimension.descriptor) == CategoricalDescriptor


def test_enumerated_serialization(valid_enumerated_data):
    """Ensure that a serialized EnumeratedDimension looks sane."""
    dimension = EnumeratedDimension.build(valid_enumerated_data)
    serialized = dimension.dump()
    assert serialized == valid_enumerated_data
