"""Tests for citrine.informatics.design_spaces serialization."""
from copy import copy
from uuid import UUID

from citrine.informatics.constraints import IngredientCountConstraint
from citrine.informatics.descriptors import CategoricalDescriptor, RealDescriptor, ChemicalFormulaDescriptor,\
    FormulationDescriptor
from citrine.informatics.design_spaces import DesignSpace, ProductDesignSpace, EnumeratedDesignSpace,\
    FormulationDesignSpace
from citrine.informatics.dimensions import ContinuousDimension, EnumeratedDimension


def valid_serialization_output(valid_data):
    return {x: y for x, y in valid_data.items() if x not in ['status', 'status_info']}


def test_simple_product_deserialization(valid_product_design_space_data):
    """Ensure that a deserialized ProductDesignSpace looks sane."""
    design_space: ProductDesignSpace = ProductDesignSpace.build(valid_product_design_space_data)
    assert design_space.name == 'my design space'
    assert design_space.description == 'does some things'
    assert type(design_space.dimensions[0]) == ContinuousDimension
    assert design_space.dimensions[0].lower_bound == 6.0
    assert type(design_space.dimensions[1]) == EnumeratedDimension
    assert design_space.dimensions[1].values == ['red']


def test_polymorphic_product_deserialization(valid_product_design_space_data):
    """Ensure that a polymorphically deserialized ProductDesignSpace looks sane."""
    design_space: ProductDesignSpace = DesignSpace.build(valid_product_design_space_data)
    assert design_space.name == 'my design space'
    assert design_space.description == 'does some things'
    assert type(design_space.dimensions[0]) == ContinuousDimension
    assert design_space.dimensions[0].lower_bound == 6.0
    assert type(design_space.dimensions[1]) == EnumeratedDimension
    assert design_space.dimensions[1].values == ['red']


def test_product_serialization(valid_product_design_space_data):
    """Ensure that a serialized ProductDesignSpace looks sane."""
    design_space = ProductDesignSpace.build(valid_product_design_space_data)
    serialized = design_space.dump()
    serialized['id'] = valid_product_design_space_data['id']
    assert serialized == valid_serialization_output(valid_product_design_space_data)


def test_simple_enumerated_deserialization(valid_enumerated_design_space_data):
    """Ensure that a deserialized EnumeratedDesignSpace looks sane.
    Deserialization is done both directly (using EnumeratedDesignSpace)
    and polymorphically (using DesignSpace)
    """
    for designSpaceClass in [DesignSpace, EnumeratedDesignSpace]:
        design_space: EnumeratedDesignSpace = designSpaceClass.build(valid_enumerated_design_space_data)
        assert design_space.name == 'my enumerated design space'
        assert design_space.description == 'enumerates some things'

        assert len(design_space.descriptors) == 3

        real, categorical, formula = design_space.descriptors

        assert type(real) == RealDescriptor
        assert real.key == 'x'
        assert real.units == ''
        assert real.lower_bound == 1.0
        assert real.upper_bound == 2.0

        assert type(categorical) == CategoricalDescriptor
        assert categorical.key == 'color'
        assert categorical.categories == {'red', 'green', 'blue'}

        assert type(formula) == ChemicalFormulaDescriptor
        assert formula.key == 'formula'

        assert len(design_space.data) == 2
        assert design_space.data[0] == {'x': 1.0, 'color': 'red', 'formula': 'C44H54Si2'}
        assert design_space.data[1] == {'x': 2.0, 'color': 'green', 'formula': 'V2O3'}


def test_enumerated_serialization(valid_enumerated_design_space_data):
    """Ensure that a serialized EnumeratedDesignSpace looks sane."""
    design_space = EnumeratedDesignSpace.build(valid_enumerated_design_space_data)
    serialized = design_space.dump()
    serialized['id'] = valid_enumerated_design_space_data['id']
    assert serialized == valid_serialization_output(valid_enumerated_design_space_data)


def test_formulation_deserialization(valid_formulation_design_space_data):
    """Ensure that a deserialized FormulationDesignSpace looks sane.
    Deserialization is done both directly (using FormulationDesignSpace)
    and polymorphically (using DesignSpace)
    """
    expected_descriptor = FormulationDescriptor('formulation')
    expected_constraint = IngredientCountConstraint(
        formulation_descriptor=expected_descriptor,
        min=0,
        max=1
    )
    for designSpaceClass in [DesignSpace, FormulationDesignSpace]:
        design_space: FormulationDesignSpace = designSpaceClass.build(valid_formulation_design_space_data)
        assert design_space.name == 'formulation design space'
        assert design_space.description == 'formulates some things'
        assert design_space.formulation_descriptor.key == expected_descriptor.key
        assert design_space.ingredients == {'foo'}
        assert design_space.labels == {'bar': {'foo'}}
        assert len(design_space.constraints) == 1
        actual_constraint: IngredientCountConstraint = next(iter(design_space.constraints))
        assert actual_constraint.formulation_descriptor == expected_descriptor
        assert actual_constraint.min == expected_constraint.min
        assert actual_constraint.max == expected_constraint.max
        assert design_space.resolution == 0.1


def test_formulation_serialization(valid_formulation_design_space_data):
    """Ensure that a serialized FormulationDesignSpace looks sane."""
    design_space = FormulationDesignSpace.build(valid_formulation_design_space_data)
    serialized = design_space.dump()
    serialized['id'] = valid_formulation_design_space_data['id']
    assert serialized == valid_serialization_output(valid_formulation_design_space_data)


def test_missing_schema_id(valid_product_design_space_data):
    """Ensure that default schema_ids are applied when missing from json."""
    missing_schema = copy(valid_product_design_space_data)
    del missing_schema["schema_id"]
    design_space: ProductDesignSpace = ProductDesignSpace.build(missing_schema)
    assert design_space.schema_id == UUID('6c16d694-d015-42a7-b462-8ef299473c9a')
