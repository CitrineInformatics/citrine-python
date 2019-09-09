"""Tests for citrine.informatics.capabilities."""
import pytest

from citrine.informatics.capabilities import ProductCapability
from citrine.informatics.descriptors import RealDescriptor, CategoricalDescriptor
from citrine.informatics.dimensions import ContinuousDimension, EnumeratedDimension


@pytest.fixture
def capability() -> ProductCapability:
    """Build a ProductCapability for testing."""
    alpha = RealDescriptor('alpha', 0, 100)
    beta = RealDescriptor('beta', 0, 100)
    gamma = CategoricalDescriptor('gamma', ['a', 'b', 'c'])
    dimensions = [
        ContinuousDimension(alpha, 0, 10),
        ContinuousDimension(beta, 0, 10),
        EnumeratedDimension(gamma, ['a', 'c'])
    ]
    return ProductCapability('my capability', 'does some things', dimensions)


def test_initialization(capability: ProductCapability):
    """Make sure the correct fields go to the correct places."""
    assert capability.name == 'my capability'
    assert capability.description == 'does some things'
    assert len(capability.dimensions) == 3
    assert capability.dimensions[0].descriptor.key == 'alpha'
    assert capability.dimensions[1].descriptor.key == 'beta'
    assert capability.dimensions[2].descriptor.key == 'gamma'
