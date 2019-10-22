"""Tests for citrine.informatics.design_spaces."""
import pytest

from citrine.informatics.descriptors import RealDescriptor, CategoricalDescriptor
from citrine.informatics.design_spaces import ProductDesignSpace, EnumeratedDesignSpace
from citrine.informatics.dimensions import ContinuousDimension, EnumeratedDimension


@pytest.fixture
def product_design_space() -> ProductDesignSpace:
    """Build a ProductDesignSpace for testing."""
    alpha = RealDescriptor('alpha', 0, 100)
    beta = RealDescriptor('beta', 0, 100)
    gamma = CategoricalDescriptor('gamma', ['a', 'b', 'c'])
    dimensions = [
        ContinuousDimension(alpha, 0, 10),
        ContinuousDimension(beta, 0, 10),
        EnumeratedDimension(gamma, ['a', 'c'])
    ]
    return ProductDesignSpace('my design space', 'does some things', dimensions)


@pytest.fixture
def enumerated_design_space() -> EnumeratedDesignSpace:
    """Build an EnumeratedDesignSpace for testing."""
    x = RealDescriptor('x', lower_bound=0.0, upper_bound=1.0)
    color = CategoricalDescriptor('color', ['r', 'g', 'b'])
    data = [dict(x=0, color='r'), dict(x=1.0, color='b')]
    return EnumeratedDesignSpace('enumerated', 'desc', descriptors=[x, color], data=data)


def test_product_initialization(product_design_space):
    """Make sure the correct fields go to the correct places."""
    assert product_design_space.name == 'my design space'
    assert product_design_space.description == 'does some things'
    assert len(product_design_space.dimensions) == 3
    assert product_design_space.dimensions[0].descriptor.key == 'alpha'
    assert product_design_space.dimensions[1].descriptor.key == 'beta'
    assert product_design_space.dimensions[2].descriptor.key == 'gamma'


def test_enumerated_initialization(enumerated_design_space):
    """Make sure the correct fields go to the correct places."""
    assert enumerated_design_space.name == 'enumerated'
    assert enumerated_design_space.description == 'desc'
    assert len(enumerated_design_space.descriptors) == 2
    assert enumerated_design_space.descriptors[0].key == 'x'
    assert enumerated_design_space.descriptors[1].key == 'color'
    assert enumerated_design_space.data == [{'x': 0.0, 'color': 'r'}, {'x': 1.0, 'color': 'b'}]
