"""Tests for citrine.informatics.dimensions."""
import pytest

from citrine.informatics.descriptors import RealDescriptor, CategoricalDescriptor
from citrine.informatics.dimensions import ContinuousDimension, EnumeratedDimension


@pytest.fixture
def continuous_dimension() -> ContinuousDimension:
    """Build a ContinuousDimension."""
    alpha = RealDescriptor('alpha', 0, 100)
    return ContinuousDimension(alpha, 3, 33)


@pytest.fixture
def enumerated_dimension() -> EnumeratedDimension:
    """Build an EnumeratedDimension."""
    color = CategoricalDescriptor('color', categories=['red', 'green', 'blue'])
    return EnumeratedDimension(color, values=['red', 'red', 'blue'])


def test_continuous_initialization(continuous_dimension):
    """Make sure the correct fields go to the correct places."""
    assert continuous_dimension.descriptor.key == 'alpha'
    assert continuous_dimension.lower_bound == 3
    assert continuous_dimension.upper_bound == 33


def test_enumerated_initialization(enumerated_dimension):
    """Make sure the correct fields go to the correct places."""
    assert enumerated_dimension.descriptor.key == 'color'
    assert enumerated_dimension.descriptor.categories == ['red', 'green', 'blue']
    assert enumerated_dimension.values == ['red', 'red', 'blue']
