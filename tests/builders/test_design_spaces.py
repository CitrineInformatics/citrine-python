"""Tests for citrine.builders.design_spaces."""
import pytest
import warnings
import numpy as np

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
    design_grid = {
        'alpha': [0, 50, 100],
        'beta': [0, 25, 50, 75, 100],
        'gamma': ['a', 'b', 'c']
    }
    basic_space = enumerate_cartesian_product(
        design_grid=design_grid,
        descriptors=[alpha, beta, gamma],
        name='basic space',
        description=''
    )
    return basic_space


@pytest.fixture
def simple_mixture_space() -> EnumeratedDesignSpace:
    """Build simple mixture space for testing."""
    formulation_grid = {
        'ing_A': [0.6, 0.7, 0.8, 0.9, 1.0],
        'ing_B': [0, 0.1, 0.2, 0.3, 0.4],
        'ing_C': [0.0, 0.01, 0.02, 0.03, 0.04, 0.05]
    }
    simple_mixture_space = enumerate_formulation_grid(
        formulation_grid=formulation_grid,
        balance_ingredient='ing_A',
        name='basic simple mixture space',
        description=''
    )
    return simple_mixture_space


@pytest.fixture
def overspec_mixture_space() -> EnumeratedDesignSpace:
    """Build overspeced mixture space for testing."""
    formulation_grid = {
        'ing_D': [0.6, 0.7],
        'ing_E': [0, 0.1, 0.2, 0.3, 0.4, 0.5],
        'ing_F': [0.0, 0.2, 0.3, 0.4, 0.5, 0.6]
    }
    overspec_mixture_space = enumerate_formulation_grid(
        formulation_grid=formulation_grid,
        balance_ingredient='ing_D',
        name='overspeced simple mixture space',
        description=''
    )
    return overspec_mixture_space


@pytest.fixture
def joint_design_space(basic_cartesian_space, simple_mixture_space) -> EnumeratedDesignSpace:
    """Build joint design space from above two examples"""
    ds_list = [basic_cartesian_space, simple_mixture_space]
    joint_space = cartesian_join_design_spaces(
        subspaces=ds_list,
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
        subspaces=ds_list,
        name='Joined enumerated design space',
        description='',
    )
    return joint_space


def test_cartesian(basic_cartesian_space):
    """Check data length, uniqueness, completeness"""
    assert len(basic_cartesian_space.data) == 45
    assert len(basic_cartesian_space.data) == len(
        set([tuple(cc.values()) for cc in basic_cartesian_space.data]))
    assert len(set([cc['alpha'] for cc in basic_cartesian_space.data])) == 3
    assert len(set([cc['beta'] for cc in basic_cartesian_space.data])) == 5
    assert len(set([cc['gamma'] for cc in basic_cartesian_space.data])) == 3


def test_formulation(simple_mixture_space, overspec_mixture_space):
    """Check data length, uniqueness, completeness for both cases above"""
    assert len(simple_mixture_space.data) == 25
    assert len(overspec_mixture_space.data) == 7
    assert len(simple_mixture_space.data) == len(
        set([tuple(cc.values()) for cc in simple_mixture_space.data]))
    assert len(overspec_mixture_space.data) == len(
        set([tuple(cc.values()) for cc in overspec_mixture_space.data]))
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
    assert len(joint_design_space.data) == len(
        set([tuple(cc.values()) for cc in joint_design_space.data]))
    assert len(large_joint_design_space.data) == len(
        set([tuple(cc.values()) for cc in large_joint_design_space.data]))


def test_exceptions(basic_cartesian_space, simple_mixture_space):
    """Test that exceptions are raised"""
    form_grids_1 = {
        'ing_D': [0.6, 1.1],
        'ing_E': [0, 0.1, 0.2, 0.3, 0.4, 0.5],
        'ing_F': [0.0, 0.2, 0.3, 0.4, 0.5, 0.6]
    }
    # Test the 'incorrect balance ingredient' error
    with pytest.raises(ValueError):
        enumerate_formulation_grid(
            formulation_grid=form_grids_1,
            balance_ingredient='wrong',
            name='invalid formulation space 1',
            description=''
        )
    # Test ingredient outside of [0,1]
    with pytest.raises(ValueError):
        enumerate_formulation_grid(
            formulation_grid=form_grids_1,
            balance_ingredient='ing_D',
            name='invalid formulation space 2',
            description=''
        )
    # Test the 'join_key' error
    form_grids_2 = {
        'ing_D': [0.6, 1.0],
        'ing_E': [0, 0.1, 0.2, 0.3, 0.4, 0.5],
        'join_key': [0.0, 0.2, 0.3, 0.4, 0.5, 0.6]
    }
    form_ds_2 = enumerate_formulation_grid(
        formulation_grid=form_grids_2,
        balance_ingredient='ing_D',
        name='dummy formulation space 2',
        description=''
    )
    with pytest.raises(ValueError):
        cartesian_join_design_spaces(
            subspaces=[
                basic_cartesian_space,
                form_ds_2
            ],
            name='invalid join space 1',
            description=''
        )
    # Test the duplicate keys error
    form_grids_3 = {
        'ing_C': [0.8, 1.0],
        'ing_D': [0, 0.1, 0.15, 0.2]
    }
    form_ds_3 = enumerate_formulation_grid(
        formulation_grid=form_grids_3,
        balance_ingredient='ing_C',
        name='dummy formulation space 3',
        description=''
    )
    with pytest.raises(ValueError):
        cartesian_join_design_spaces(
            subspaces=[
                simple_mixture_space,
                form_ds_3
            ],
            name='invalid join space 2',
            description=''
        )


def test_warnings():
    """Test that warnings are raised"""
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        with pytest.warns(UserWarning):
            too_big_formulation_grid = {
                'ing_F': np.linspace(0, 1),
                'ing_G': np.linspace(0, 1),
                'ing_H': np.linspace(0, 1),
                'ing_I': np.linspace(0, 1),
                'ing_J': np.linspace(0, 1),
                'ing_K': np.linspace(0, 1)
            }
            too__big_mixture_space = enumerate_formulation_grid(
                formulation_grid=too_big_formulation_grid,
                balance_ingredient='ing_K',
                name='too big mixture space',
                description=''
            )

