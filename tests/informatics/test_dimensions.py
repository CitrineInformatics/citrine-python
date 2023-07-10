"""Tests for citrine.informatics.dimensions."""
import pytest

from citrine.informatics.descriptors import RealDescriptor, CategoricalDescriptor, \
    IntegerDescriptor
from citrine.informatics.dimensions import ContinuousDimension, EnumeratedDimension, \
    IntegerDimension


@pytest.fixture
def continuous_dimension() -> ContinuousDimension:
    """Build a ContinuousDimension."""
    alpha = RealDescriptor('alpha', lower_bound=0, upper_bound=100, units="")
    return ContinuousDimension(alpha, lower_bound=3, upper_bound=33)


@pytest.fixture
def enumerated_dimension() -> EnumeratedDimension:
    """Build an EnumeratedDimension."""
    color = CategoricalDescriptor('color', categories={'red', 'green', 'blue'})
    return EnumeratedDimension(color, values=['red', 'red', 'blue'])


def test_continuous_initialization(continuous_dimension):
    """Make sure the correct fields go to the correct places."""
    assert continuous_dimension.descriptor.key == 'alpha'
    assert continuous_dimension.lower_bound == 3
    assert continuous_dimension.upper_bound == 33


def test_continuous_bounds():
    """Test bounds are assigned correctly, even when bounds are == 0"""
    beta = RealDescriptor('beta', lower_bound=-10, upper_bound=10, units="")
    lower_none = ContinuousDimension(beta, upper_bound=0)
    assert lower_none.lower_bound == -10
    assert lower_none.upper_bound == 0

    upper_none = ContinuousDimension(beta, lower_bound=0)
    assert upper_none.lower_bound == 0
    assert upper_none.upper_bound == 10


def test_integer_bounds():
    """Test bounds are assigned correctly, even when bounds are == 0"""
    beta = IntegerDescriptor('beta', lower_bound=-10, upper_bound=10)
    lower_none = IntegerDimension(beta, upper_bound=0)
    assert lower_none.lower_bound == -10
    assert lower_none.upper_bound == 0

    upper_none = IntegerDimension(beta, lower_bound=0)
    assert upper_none.lower_bound == 0
    assert upper_none.upper_bound == 10


def test_enumerated_initialization(enumerated_dimension):
    """Make sure the correct fields go to the correct places."""
    assert enumerated_dimension.descriptor.key == 'color'
    assert enumerated_dimension.descriptor.categories == {'red', 'green', 'blue'}
    assert enumerated_dimension.values == ['red', 'red', 'blue']
