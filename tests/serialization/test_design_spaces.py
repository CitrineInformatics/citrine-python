"""Tests for citrine.informatics.design_spaces serialization."""

from copy import deepcopy

import pytest

from citrine.informatics.constraints import IngredientCountConstraint
from citrine.informatics.descriptors import FormulationDescriptor
from citrine.informatics.design_spaces import (
    DesignSubspace,
    FormulationDesignSpace,
    ProductDesignSpace,
    TopLevelDesignSpace,
)
from citrine.informatics.dimensions import ContinuousDimension, EnumeratedDimension

from . import design_space_serialization_check


def test_product_deserialization(valid_product_design_space_data):
    """Ensure that a deserialized ProductDesignSpace looks sane."""
    for designSpaceClass in [ProductDesignSpace, TopLevelDesignSpace]:
        data = deepcopy(valid_product_design_space_data)
        design_space: ProductDesignSpace = designSpaceClass.build(data)
        assert design_space.name == "my design space"
        assert design_space.description == "does some things"
        assert type(design_space.dimensions[0]) == ContinuousDimension
        assert design_space.dimensions[0].lower_bound == 6.0
        assert type(design_space.dimensions[1]) == EnumeratedDimension
        assert design_space.dimensions[1].values == ["red"]
        assert type(design_space.subspaces[0]) == FormulationDesignSpace
        assert type(design_space.subspaces[1]) == FormulationDesignSpace
        assert design_space.subspaces[1].ingredients == {"baz"}


def test_product_serialization(valid_product_design_space_data):
    """Ensure that a serialized ProductDesignSpace looks sane."""
    original_data = deepcopy(valid_product_design_space_data)
    design_space = ProductDesignSpace.build(valid_product_design_space_data)
    serialized = design_space.dump()
    serialized["id"] = valid_product_design_space_data["id"]
    serialized_subspaces = serialized["instance"]["subspaces"]
    original_subspaces = original_data["data"]["instance"]["subspaces"]
    assert serialized_subspaces[0] == original_subspaces[0]
    assert serialized_subspaces[1] == original_subspaces[1]


def test_formulation_deserialization(valid_formulation_design_space_data):
    """Ensure that a deserialized FormulationDesignSpace looks sane.
    Deserialization is done both directly (using FormulationDesignSpace)
    and polymorphically (using DesignSubspace)
    """
    expected_descriptor = FormulationDescriptor.hierarchical()
    expected_constraint = IngredientCountConstraint(
        formulation_descriptor=expected_descriptor, min=0, max=1
    )
    for designSpaceClass in [DesignSubspace, FormulationDesignSpace]:
        design_space: FormulationDesignSpace = designSpaceClass.build(
            valid_formulation_design_space_data
        )
        assert design_space.name == "formulation design space"
        assert design_space.description == "formulates some things"
        assert design_space.formulation_descriptor.key == expected_descriptor.key
        assert design_space.ingredients == {"foo"}
        assert design_space.labels == {"bar": {"foo"}}
        assert design_space.untested_ingredients == {"qux"}
        assert len(design_space.constraints) == 1
        actual_constraint: IngredientCountConstraint = next(iter(design_space.constraints))
        assert actual_constraint.formulation_descriptor == expected_descriptor
        assert actual_constraint.min == expected_constraint.min
        assert actual_constraint.max == expected_constraint.max
        assert design_space.resolution == 0.1


def test_formulation_serialization(valid_formulation_design_space_data):
    """Ensure that a serialized FormulationDesignSpace looks sane."""
    design_space_serialization_check(valid_formulation_design_space_data, FormulationDesignSpace)


def test_formulation_without_untested_ingredients(valid_formulation_design_space_data):
    """A payload lacking untested_ingredients still deserializes (field is optional).

    Pins backward compatibility with design spaces that predate the field: the
    field must stay optional, so older payloads without the key don't fail to build.
    """
    data = deepcopy(valid_formulation_design_space_data)
    del data["untested_ingredients"]
    design_space: FormulationDesignSpace = FormulationDesignSpace.build(data)
    assert design_space.untested_ingredients is None


def test_invalid_design_subspace_type(invalid_design_subspace_data):
    """Ensures we raise proper exception when an invalid type is used."""
    with pytest.raises(ValueError):
        DesignSubspace.build(invalid_design_subspace_data)
