"""Tests for citrine.informatics.design_spaces."""
import pytest

from citrine.informatics.constraints import IngredientCountConstraint
from citrine.informatics.data_sources import DataSource, CSVDataSource
from citrine.informatics.descriptors import RealDescriptor, CategoricalDescriptor, FormulationDescriptor
from citrine.informatics.design_spaces import *
from citrine.informatics.dimensions import ContinuousDimension, EnumeratedDimension
from citrine.resources.file_link import FileLink


@pytest.fixture
def product_design_space() -> ProductDesignSpace:
    """Build a ProductDesignSpace for testing."""
    alpha = RealDescriptor('alpha', 0, 100, "")
    beta = RealDescriptor('beta', 0, 100, "")
    gamma = CategoricalDescriptor('gamma', ['a', 'b', 'c'])
    dimensions = [
        ContinuousDimension(alpha, 0, 10),
        ContinuousDimension(beta, 0, 10),
        EnumeratedDimension(gamma, ['a', 'c'])
    ]
    return ProductDesignSpace(name='my design space', description='does some things', dimensions=dimensions)


@pytest.fixture
def enumerated_design_space() -> EnumeratedDesignSpace:
    """Build an EnumeratedDesignSpace for testing."""
    x = RealDescriptor('x', lower_bound=0.0, upper_bound=1.0, units='')
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


def test_formulation_ingredient_set():
    """Make sure ingredients can be specified as a list and are converted to a set"""
    descriptor = FormulationDescriptor('formulation')
    constraint = IngredientCountConstraint(
        formulation_descriptor=descriptor,
        min=1,
        max=1
    )
    design_space = FormulationDesignSpace(
        name="Formulation design space",
        description="",
        formulation_descriptor=descriptor,
        ingredients=['ingredient'],
        constraints={constraint}
    )
    assert design_space.ingredients == {'ingredient'}

    design_space.ingredients = ['ing 1', 'ing 2']
    assert design_space.ingredients == {'ing 1', 'ing 2'}


def test_data_source_build(valid_data_source_design_space_dict):
    ds = DesignSpace.build(valid_data_source_design_space_dict)
    assert ds.name == valid_data_source_design_space_dict["config"]["name"]
    assert ds.data_source == DataSource.build(valid_data_source_design_space_dict["config"]["data_source"])


def test_data_source_create():
    ds = DataSourceDesignSpace(
        name="Test",
        description="ing",
        data_source=CSVDataSource(
            file_link=FileLink(filename="foo.csv", url="http://example.com/bar.csv"),
            column_definitions={
                "foo": RealDescriptor(key="bar", lower_bound=0, upper_bound=100, units="kg")
            }
        )
    )
    round_robin = DesignSpace.build(ds.dump())
    assert ds.name == round_robin.name
    assert ds.description == round_robin.description
    assert ds.data_source == round_robin.data_source
    assert "DataSource" in str(ds)
