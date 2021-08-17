"""Tests for citrine.builders.design_spaces."""
import pytest
import warnings
import numpy as np

from citrine.informatics.descriptors import RealDescriptor, CategoricalDescriptor
from citrine.informatics.design_spaces import EnumeratedDesignSpace
from citrine.builders.design_spaces import enumerate_cartesian_product, \
    enumerate_formulation_grid, cartesian_join_design_spaces, enumerated_to_data_source, migrate_enumerated_design_space
from tests.utils.fakes.fake_dataset import FakeDataset
from tests.utils.fakes.fake_project import FakeProject


@pytest.fixture(scope="module")
def to_clean():
    """Clean up files, even if a test fails"""
    import os
    files_to_clean = []
    yield files_to_clean
    for f in files_to_clean:
        try:
            os.remove(f)
        except FileNotFoundError:
            pass


@pytest.fixture
def basic_cartesian_space() -> EnumeratedDesignSpace:
    """Build basic cartesian space for testing."""
    alpha = RealDescriptor('alpha', lower_bound=0, upper_bound=100, units="")
    beta = RealDescriptor('beta', lower_bound=0, upper_bound=100, units="")
    gamma = CategoricalDescriptor('gamma', categories=['a', 'b', 'c'])
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


def test_formulation_oversize_warnings():
    """Test that oversized formulation grid warnings are raised"""
    with pytest.raises(UserWarning, match="1562500000"):
        # Fail on warning (so code stops running)
        with warnings.catch_warnings():
            warnings.simplefilter('error')
            too_big_formulation_grid = {
                'ing_F': np.linspace(0, 1, 50),
                'ing_G': np.linspace(0, 1, 50),
                'ing_H': np.linspace(0, 1, 50),
                'ing_I': np.linspace(0, 1, 50),
                'ing_J': np.linspace(0, 1, 50),
                'ing_K': np.linspace(0, 1, 50)
            }
            enumerate_formulation_grid(
                formulation_grid=too_big_formulation_grid,
                balance_ingredient='ing_K',
                name='too big mixture space',
                description=''
            )


def test_enumerated_oversize_warnings():
    """Test that oversized enumerated space warnings are raised"""
    with pytest.raises(UserWarning, match="648000000"):
        # Fail on warning (so code stops running)
        with warnings.catch_warnings():
            warnings.simplefilter('error')
            delta = RealDescriptor('delta', lower_bound=0, upper_bound=100, units="")
            epsilon = RealDescriptor('epsilon', lower_bound=0, upper_bound=100, units="")
            zeta = RealDescriptor('zeta', lower_bound=0, upper_bound=100, units="")
            too_big_enumerated_grid = {
                'delta': np.linspace(0, 100, 600),
                'epsilon': np.linspace(0, 100, 600),
                'zeta': np.linspace(0, 100, 600),
            }
            enumerate_cartesian_product(
                design_grid=too_big_enumerated_grid,
                descriptors=[delta, epsilon, zeta],
                name='too big space',
                description=''
            )


def test_joined_oversize_warnings(large_joint_design_space):
    """Test that oversized joined space warnings are raised"""
    with pytest.raises(UserWarning, match="239203125"):
        # Fail on warning (so code stops running)
        with warnings.catch_warnings():
            warnings.simplefilter('error')

            delta = RealDescriptor('delta', lower_bound=0, upper_bound=100, units="")
            epsilon = RealDescriptor('epsilon', lower_bound=0, upper_bound=100, units="")
            zeta = CategoricalDescriptor('zeta', categories=['a', 'b', 'c'])
            design_grid = {
                'delta': [0, 50, 100],
                'epsilon': [0, 25, 50, 75, 100],
                'zeta': ['a', 'b', 'c']
            }
            basic_space_2 = enumerate_cartesian_product(
                design_grid=design_grid,
                descriptors=[delta, epsilon, zeta],
                name='basic space 2',
                description=''
            )

            eta = RealDescriptor('eta', lower_bound=0, upper_bound=100, units="")
            theta = RealDescriptor('theta', lower_bound=0, upper_bound=100, units="")
            iota = CategoricalDescriptor('iota', categories=['a', 'b', 'c'])
            design_grid = {
                'eta': [0, 50, 100],
                'theta': [0, 25, 50, 75, 100],
                'iota': ['a', 'b', 'c']
            }
            basic_space_3 = enumerate_cartesian_product(
                design_grid=design_grid,
                descriptors=[eta, theta, iota],
                name='basic space 3',
                description=''
            )

            cartesian_join_design_spaces(
                subspaces=[
                    basic_space_2,
                    basic_space_3,
                    large_joint_design_space
                ],
                name='too big join space',
                description=''
            )


def test_enumerated_to_data_source(basic_cartesian_space, to_clean):
    """Test enumerated_to_data_source conversion"""
    expected_fname = basic_cartesian_space.name.replace(" ", "_") + "_source_data.csv"
    to_clean.append(expected_fname)

    dataset = FakeDataset()
    result = enumerated_to_data_source(
        enumerated_ds=basic_cartesian_space, dataset=dataset)

    assert result.name == basic_cartesian_space.name
    assert result.description == basic_cartesian_space.description
    assert result.data_source.file_link.url == expected_fname
    expected_keys = {x.key for x in basic_cartesian_space.descriptors}
    assert {x for x in result.data_source.column_definitions.keys()} == expected_keys


def test_migrate_enumerated(basic_cartesian_space, to_clean):
    """Test migrate_enumerated_design_space with fakes."""
    fname = "foo.csv"  # not to conflict with the above test
    to_clean.append(fname)

    project = FakeProject(name="foo", description="bar")
    dataset = FakeDataset()
    old = project.design_spaces.register(basic_cartesian_space)

    # first test that it works when it should
    new = migrate_enumerated_design_space(
        project=project, uid=old.uid, dataset=dataset, filename=fname)
    assert new.name == old.name
    # the other equality logic is tested in test_enumerated_to_data_source
    assert project.design_spaces.get(old.uid).archived

    # test that it doesn't work when it shouldn't
    with pytest.raises(ValueError):
        migrate_enumerated_design_space(
            project=project, uid=new.uid, dataset=dataset, filename=fname)

    # it failed, so it shouldn't have archived the old one
    assert not project.design_spaces.get(new.uid).archived

    # test that it works for a design space that cannot be archived because it is in use
    old_in_use = project.design_spaces.register(basic_cartesian_space)
    project.design_spaces.in_use[old_in_use.uid] = True
    migrate_enumerated_design_space(
        project=project, uid=old_in_use.uid, dataset=dataset, filename=fname)
