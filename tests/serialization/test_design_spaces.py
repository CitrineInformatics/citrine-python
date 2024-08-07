"""Tests for citrine.informatics.design_spaces serialization."""
from copy import copy, deepcopy
from uuid import UUID

import pytest

from . import design_space_serialization_check, valid_serialization_output
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
        assert design_space.subspaces[0].uid is None
        assert type(design_space.subspaces[1]) == FormulationDesignSpace
        assert design_space.subspaces[1].uid is None
        assert design_space.subspaces[1].ingredients == {'baz'}


def test_product_serialization(valid_product_design_space_data):
    """Ensure that a serialized ProductDesignSpace looks sane."""
    original_data = deepcopy(valid_product_design_space_data)
    design_space = ProductDesignSpace.build(valid_product_design_space_data)
    serialized = design_space.dump()
    serialized['id'] = valid_product_design_space_data['id']
    assert serialized['instance']['subspaces'][0] == original_data['data']['instance']['subspaces'][0]
    assert serialized['instance']['subspaces'][1] == original_data['data']['instance']['subspaces'][1]


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
        assert design_space.data[0] == {'x': '1', 'color': 'red', 'formula': 'C44H54Si2'}
        assert design_space.data[1] == {'x': '2.0', 'color': 'green', 'formula': 'V2O3'}


def test_enumerated_serialization_data_int_deprecated(valid_enumerated_design_space_data):
    design_space = EnumeratedDesignSpace.build(valid_enumerated_design_space_data)
    with pytest.deprecated_call():
        design_space.data = [dict(x=1, color='red', formula='C44H54Si2')]


def test_enumerated_serialization_data_float_deprecated(valid_enumerated_design_space_data):
    design_space = EnumeratedDesignSpace.build(valid_enumerated_design_space_data)
    with pytest.deprecated_call():
        design_space.data = [dict(x=1.0, color='red', formula='C44H54Si2')]


def test_enumerated_serialization(valid_enumerated_design_space_data):
    """Ensure that a serialized EnumeratedDesignSpace looks sane."""
    design_space_serialization_check(valid_enumerated_design_space_data, EnumeratedDesignSpace)


def test_formulation_deserialization(valid_formulation_design_space_data):
    """Ensure that a deserialized FormulationDesignSpace looks sane.
    Deserialization is done both directly (using FormulationDesignSpace)
    and polymorphically (using DesignSpace)
    """
    expected_descriptor = FormulationDescriptor.hierarchical()
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
    design_space_serialization_check(valid_formulation_design_space_data, FormulationDesignSpace)
