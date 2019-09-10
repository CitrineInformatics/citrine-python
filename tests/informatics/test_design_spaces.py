"""Tests for citrine.informatics.design_spaces."""
import pytest

from citrine.informatics.design_spaces import ProductDesignSpace
from citrine.informatics.descriptors import RealDescriptor, CategoricalDescriptor
from citrine.informatics.dimensions import ContinuousDimension, EnumeratedDimension


@pytest.fixture
def design_space() -> ProductDesignSpace:
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


def test_initialization(design_space):
    """Make sure the correct fields go to the correct places."""
    assert design_space.name == 'my design space'
    assert design_space.description == 'does some things'
    assert len(design_space.dimensions) == 3
    assert design_space.dimensions[0].descriptor.key == 'alpha'
    assert design_space.dimensions[1].descriptor.key == 'beta'
    assert design_space.dimensions[2].descriptor.key == 'gamma'
