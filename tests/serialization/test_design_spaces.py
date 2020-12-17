"""Tests for citrine.informatics.design_spaces serialization."""
from copy import copy, deepcopy
from uuid import UUID

from . import serialization_check, valid_serialization_output
from citrine.informatics.constraints import IngredientCountConstraint
from citrine.informatics.descriptors import CategoricalDescriptor, RealDescriptor, ChemicalFormulaDescriptor,\
    FormulationDescriptor
from citrine.informatics.design_spaces import DesignSpace, ProductDesignSpace, EnumeratedDesignSpace,\
    FormulationDesignSpace
from citrine.informatics.dimensions import ContinuousDimension, EnumeratedDimension


def test_product_deserialization(valid_product_design_space_data):
    """Ensure that a deserialized ProductDesignSpace looks sane."""
    for designSpaceClass in [ProductDesignSpace, DesignSpace]:
        data = deepcopy(valid_product_design_space_data)
        design_space: ProductDesignSpace = designSpaceClass.build(data)
        assert design_space.name == 'my design space'
        assert design_space.description == 'does some things'
        assert type(design_space.dimensions[0]) == ContinuousDimension
        assert design_space.dimensions[0].lower_bound == 6.0
        assert type(design_space.dimensions[1]) == EnumeratedDimension
        assert design_space.dimensions[1].values == ['red']
        assert type(design_space.subspaces[0]) == FormulationDesignSpace
        assert type(design_space.subspaces[0].uid) == UUID
        assert type(design_space.subspaces[1]) == FormulationDesignSpace
        assert design_space.subspaces[1].uid is None
        assert design_space.subspaces[1].ingredients == {'baz'}


def test_product_serialization(valid_product_design_space_data):
    """Ensure that a serialized ProductDesignSpace looks sane."""
    original_data = deepcopy(valid_product_design_space_data)
    design_space = ProductDesignSpace.build(valid_product_design_space_data)
    serialized = design_space.dump()
    serialized['id'] = valid_product_design_space_data['id']
    assert serialized['config']['subspaces'][0] == original_data['config']['subspaces'][0]['id']
    assert serialized['config']['subspaces'][1] == original_data['config']['subspaces'][1]['instance']


def test_old_product_serialization(old_valid_product_design_space_data):
    """Ensure that the old version of the product design space can be (de)serialized.
    The previous version had no `subspaces` field and had type `Univariate`.
    Some on-platform assets are saved this way, and should be converted seamlessly
    into ProductDesignSpaces.
    """
    design_space = ProductDesignSpace.build(old_valid_product_design_space_data)
    assert design_space.subspaces == []
    assert design_space.typ == 'ProductDesignSpace'
    serialized = design_space.dump()
    serialized['id'] = old_valid_product_design_space_data['id']
    serialized['config']['type'] = 'Univariate'
    del serialized['config']['subspaces']
    assert serialized == valid_serialization_output(old_valid_product_design_space_data)


def test_enumerated_deserialization(valid_enumerated_design_space_data):
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
    serialization_check(valid_enumerated_design_space_data, EnumeratedDesignSpace)


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
    serialization_check(valid_formulation_design_space_data, FormulationDesignSpace)
