"""Tests for citrine.informatics.design_spaces."""
import pytest

from citrine.informatics.descriptors import RealDescriptor, CategoricalDescriptor
from citrine.informatics.design_spaces import EnumeratedDesignSpace
from citrine.builders.design_spaces import enumerate_cartesian_product, \
    enumerate_simple_mixture_cartesian_product, cartesian_join_design_spaces


@pytest.fixture
def basic_cartesian_space() -> EnumeratedDesignSpace:
    """Build basic cartesian space for testing."""
    alpha = RealDescriptor('alpha', 0, 100)
    beta = RealDescriptor('beta', 0, 100)
    gamma = CategoricalDescriptor('gamma', ['a', 'b', 'c'])
    design_grids = {
        'alpha': [0, 50, 100],
        'beta': [0, 25, 50, 75, 100],
        'gamma': ['a', 'b', 'c']
    }
    basic_space = enumerate_cartesian_product(
        design_grids=design_grids,
        descriptors=[alpha, beta, gamma],
        name='basic space',
        description=''
    )
    return basic_space


@pytest.fixture
def simple_mixture_space() -> EnumeratedDesignSpace:
    """Build simple mixture space for testing."""
    ing_A = RealDescriptor('ing_A', 0, 1)
    ing_B = RealDescriptor('ing_B', 0, 1)
    ing_C = RealDescriptor('ing_C', 0, 1)
    formulation_grids = {
        'ing_A': [0.6, 0.7, 0.8, 0.9, 1.0],
        'ing_B': [0, 0.1, 0.2, 0.3, 0.4],
        'ing_C': [0.0, 0.01, 0.02, 0.03, 0.04, 0.05]
    }
    simple_mixture_space = enumerate_simple_mixture_cartesian_product(
        formulation_grids=formulation_grids,
        balance_component='ing_A',
        descriptors=[ing_A, ing_B, ing_C],
        name='basic simple mixture space',
        description=''
    )
    return simple_mixture_space


@pytest.fixture
def joint_design_space() -> EnumeratedDesignSpace:
    """Build joint design space from above two examples"""
    ds_list = [basic_cartesian_space, simple_mixture_space]
    joint_space = cartesian_join_design_spaces(
        design_space_list=ds_list,
        name='Joined enumerated design space',
        description='',
    )
    return joint_space


def test_enumerated_cartesian(basic_cartesian_space):
    """Check data length"""
    assert len(basic_cartesian_space.data) == 45


def test_simple_mixture(simple_mixture_space):
    """Check data length"""
    assert len(simple_mixture_space.data) == 25


def test_joined(joint_design_space):
    """Check data length and number of descriptors"""
    assert len(joint_design_space.data) == 1125
    assert len(joint_design_space.descriptors) == 6
