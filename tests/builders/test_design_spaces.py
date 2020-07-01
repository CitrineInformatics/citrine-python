"""Tests for citrine.informatics.design_spaces."""
import pytest

from citrine.informatics.descriptors import RealDescriptor, CategoricalDescriptor
from citrine.informatics.design_spaces import EnumeratedDesignSpace
from citrine.builders.design_spaces import enumerate_cartesian_product, \
    enumerate_formulation_grid, cartesian_join_design_spaces


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
    simple_mixture_space = enumerate_formulation_grid(
        formulation_grids=formulation_grids,
        balance_component='ing_A',
        descriptors=[ing_A, ing_B, ing_C],
        name='basic simple mixture space',
        description=''
    )
    return simple_mixture_space


@pytest.fixture
def overspec_mixture_space() -> EnumeratedDesignSpace:
    """Build overspeced mixture space for testing."""
    ing_D = RealDescriptor('ing_D', 0, 1)
    ing_E = RealDescriptor('ing_E', 0, 1)
    ing_F = RealDescriptor('ing_F', 0, 1)
    formulation_grids = {
        'ing_D': [0.6, 0.7],
        'ing_E': [0, 0.1, 0.2, 0.3, 0.4, 0.5],
        'ing_F': [0.0, 0.25, 0.5, 0.75, 1]
    }
    overspec_mixture_space = enumerate_formulation_grid(
        formulation_grids=formulation_grids,
        balance_component='ing_D',
        descriptors=[ing_D, ing_E, ing_F],
        name='overspeced simple mixture space',
        description=''
    )
    return overspec_mixture_space


@pytest.fixture
def joint_design_space(basic_cartesian_space, simple_mixture_space) -> EnumeratedDesignSpace:
    """Build joint design space from above two examples"""
    ds_list = [basic_cartesian_space, simple_mixture_space]
    joint_space = cartesian_join_design_spaces(
        design_space_list=ds_list,
        name='Joined enumerated design space',
        description='',
    )
    return joint_space


@pytest.fixture
def large_joint_design_space(
    basic_cartesian_space,
    simple_mixture_space,
    overspec_mixture_space
) -> EnumeratedDesignSpace:
    """Build joint design space from above two examples"""
    ds_list = [basic_cartesian_space, simple_mixture_space, overspec_mixture_space]
    joint_space = cartesian_join_design_spaces(
        design_space_list=ds_list,
        name='Joined enumerated design space',
        description='',
    )
    return joint_space


def test_cartesian(basic_cartesian_space):
    """Check data length, uniqueness, completeness"""
    assert len(basic_cartesian_space.data) == 45
    assert len(basic_cartesian_space.data) == len(set(basic_cartesian_space.data))
    assert len(set([cc['alpha'] for cc in basic_cartesian_space.data])) == 3
    assert len(set([cc['beta'] for cc in basic_cartesian_space.data])) == 5
    assert len(set([cc['gamma'] for cc in basic_cartesian_space.data])) == 3


def test_formulation(simple_mixture_space, overspec_mixture_space):
    """Check data length, uniqueness, completeness for both cases above"""
    assert len(simple_mixture_space.data) == 25
    assert len(overspec_mixture_space.data) == 7
    assert len(simple_mixture_space.data) == len(set(simple_mixture_space.data))
    assert len(overspec_mixture_space) == len(set(overspec_mixture_space))
    # Check that all members of ing_B and ing_C values made it into candidates
    assert len(set([cc['ing_B'] for cc in simple_mixture_space.data])) == 5
    assert len(set([cc['ing_C'] for cc in simple_mixture_space.data])) == 6
    # Check that correct number of members for ing_E and ing_F were excluded
    assert len(set([cc['ing_E'] for cc in overspec_mixture_space.data])) == 5
    assert len(set([cc['ing_F'] for cc in overspec_mixture_space.data])) == 4


def test_joined(joint_design_space, large_joint_design_space):
    """Check data length, number of descriptors for 2 and more spaces"""
    assert len(joint_design_space.data) == 1125
    assert len(large_joint_design_space.data) == 7875
    assert len(joint_design_space.descriptors) == 6
    assert len(large_joint_design_space.descriptors) == 9
    assert len(joint_design_space) == len(set(joint_design_space))
    assert len(large_joint_design_space) == len(set(large_joint_design_space))
