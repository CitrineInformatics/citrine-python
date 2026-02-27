"""Tests for citrine.informatics.design_spaces."""
import uuid

import pytest

from citrine.informatics.constraints import IngredientCountConstraint
from citrine.informatics.data_sources import DataSource, GemTableDataSource
from citrine.informatics.descriptors import FormulationDescriptor, RealDescriptor, \
    CategoricalDescriptor, IntegerDescriptor
from citrine.informatics.design_spaces import *
from citrine.informatics.dimensions import ContinuousDimension, EnumeratedDimension, \
    IntegerDimension


@pytest.fixture
def product_design_space() -> ProductDesignSpace:
    """Build a ProductDesignSpace for testing."""
    alpha = RealDescriptor('alpha', lower_bound=0, upper_bound=100, units="")
    beta = IntegerDescriptor('beta', lower_bound=0, upper_bound=100)
    gamma = CategoricalDescriptor('gamma', categories=['a', 'b', 'c'])
    dimensions = [
        ContinuousDimension(alpha, lower_bound=0, upper_bound=10),
        IntegerDimension(beta, lower_bound=0, upper_bound=10),
        EnumeratedDimension(gamma, values=['a', 'c'])
    ]
    return ProductDesignSpace(name='my design space', description='does some things', dimensions=dimensions)


@pytest.fixture
def formulation_design_space() -> FormulationDesignSpace:
    desc = FormulationDescriptor.hierarchical()
    return FormulationDesignSpace(
        name="Formulation DS",
        description="Does formulations",
        formulation_descriptor=desc,
        ingredients={"dog", "cat", "bird"},
        labels={"canine": {"dog"}, "feline": {"cat"}},
        constraints={
            IngredientCountConstraint(formulation_descriptor=desc, min=1, max=2)
        }
    )


@pytest.fixture
def hierarchical_design_space(material_node_definition) -> HierarchicalDesignSpace:
    return HierarchicalDesignSpace(
        name="Hierarchical DS",
        description="Does things in levels",
        root=material_node_definition,
        subspaces=[material_node_definition],
        data_sources=[
            GemTableDataSource(table_id=uuid.uuid4(), table_version=2)
        ]
    )


@pytest.fixture
def material_node_definition(formulation_design_space) -> MaterialNodeDefinition:
    temp = RealDescriptor('temperature', lower_bound=0.0, upper_bound=1.0, units='')
    temp_dimension = ContinuousDimension(temp, lower_bound=0.1, upper_bound=0.9)

    color = CategoricalDescriptor('color', categories={'r', 'g', 'b'})
    color_dimension = EnumeratedDimension(color, values=['g', 'b'])

    link = TemplateLink(
        material_template=uuid.uuid4(),
        process_template=uuid.uuid4(),
        material_template_name="Material Template Name",
        process_template_name="Process Template Name"
    )

    return MaterialNodeDefinition(
        name=f"Special Material-{uuid.uuid4()}",
        scope="Special Scope",
        formulation_subspace=formulation_design_space,
        template_link=link,
        attributes=[temp_dimension, color_dimension],
        display_name="Special Material"
    )


def test_product_initialization(product_design_space):
    """Make sure the correct fields go to the correct places."""
    assert product_design_space.name == 'my design space'
    assert product_design_space.description == 'does some things'
    assert len(product_design_space.dimensions) == 3
    assert product_design_space.dimensions[0].descriptor.key == 'alpha'
    assert product_design_space.dimensions[1].descriptor.key == 'beta'
    assert product_design_space.dimensions[2].descriptor.key == 'gamma'


def test_hierarchical_initialization(hierarchical_design_space):
    assert hierarchical_design_space.root.formulation_subspace is not None
    assert len(hierarchical_design_space.subspaces) == 1
    assert "HierarchicalDesignSpace" in str(hierarchical_design_space)
    assert "MaterialNodeDefinition" in str(hierarchical_design_space.root)

    # Check that FDS is not wrapped as an "entity" during dumps
    hds_data = hierarchical_design_space.dump()
    fds_data = hds_data["instance"]["root"]["formulation"]
    assert "formulation_descriptor" in fds_data


def test_data_source_build(valid_data_source_design_space_dict):
    ds = DataSourceDesignSpace.build(valid_data_source_design_space_dict)
    assert ds.name == valid_data_source_design_space_dict["name"]
    assert ds.description == valid_data_source_design_space_dict["description"]
    assert ds.data_source == DataSource.build(valid_data_source_design_space_dict["data_source"])
    assert str(ds) == f"<DataSourceDesignSpace '{ds.name}'>"


def test_data_source_initialization(valid_data_source_design_space_dict):
    data = valid_data_source_design_space_dict
    data_source = DataSource.build(data["data_source"])
    ds = DataSourceDesignSpace(name=data["name"],
                               description=data["description"],
                               data_source=data_source)
    assert ds.name == data["name"]
    assert ds.description == data["description"]
    assert ds.data_source.dump() == data["data_source"]
