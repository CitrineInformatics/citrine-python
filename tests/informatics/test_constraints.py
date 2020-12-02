"""Tests for citrine.informatics.constraints."""
import pytest

from citrine.informatics.constraints import *
from citrine.informatics.descriptors import FormulationDescriptor

formulation_descriptor = FormulationDescriptor('formulation')


@pytest.fixture
def scalar_range_constraint() -> ScalarRangeConstraint:
    """Build a ScalarRangeConstraint."""
    return ScalarRangeConstraint(
        descriptor_key='z',
        min=1.0,
        max=10.0,
        min_inclusive=False
    )


@pytest.fixture
def categorical_constraint() -> CategoricalConstraint:
    """Build a CategoricalConstraint."""
    return CategoricalConstraint(
        descriptor_key='x',
        acceptable_categories=['y', 'z']
    )


@pytest.fixture
def ingredient_fraction_constraint() -> IngredientFractionConstraint:
    """Build an IngredientFractionConstraint."""
    return IngredientFractionConstraint(
        formulation_descriptor=formulation_descriptor,
        ingredient='foo',
        min=0.0,
        max=1.0,
        is_required=False
    )


@pytest.fixture
def ingredient_count_constraint() -> IngredientCountConstraint:
    """Build an IngredientCountConstraint."""
    return IngredientCountConstraint(
        formulation_descriptor=formulation_descriptor,
        min=0,
        max=1,
        label='bar'
    )


@pytest.fixture
def label_fraction_constraint() -> LabelFractionConstraint:
    """Build a LabelFractionConstraint."""
    return LabelFractionConstraint(
        formulation_descriptor=formulation_descriptor,
        label='bar',
        min=0.0,
        max=1.0,
        is_required=False
    )


def test_scalar_range_initialization(scalar_range_constraint):
    """Make sure the correct fields go to the correct places."""
    assert scalar_range_constraint.descriptor_key == 'z'
    assert scalar_range_constraint.min == 1.0
    assert scalar_range_constraint.max == 10.0
    assert not scalar_range_constraint.min_inclusive
    assert scalar_range_constraint.max_inclusive
    assert scalar_range_constraint.session is None


def test_categorical_initialization(categorical_constraint):
    """Make sure the correct fields go to the correct places."""
    assert categorical_constraint.descriptor_key == 'x'
    assert categorical_constraint.acceptable_categories == ['y', 'z']


def test_ingredient_fraction_initialization(ingredient_fraction_constraint):
    """Make sure the correct fields go to the correct places."""
    assert ingredient_fraction_constraint.formulation_descriptor == formulation_descriptor
    assert ingredient_fraction_constraint.ingredient == 'foo'
    assert ingredient_fraction_constraint.min == 0.0
    assert ingredient_fraction_constraint.max == 1.0
    assert not ingredient_fraction_constraint.is_required
    assert ingredient_fraction_constraint.session is None


def test_ingredient_count_initialization(ingredient_count_constraint):
    """Make sure the correct fields go to the correct places."""
    assert ingredient_count_constraint.formulation_descriptor == formulation_descriptor
    assert ingredient_count_constraint.min == 0
    assert ingredient_count_constraint.max == 1
    assert ingredient_count_constraint.label == 'bar'
    assert ingredient_count_constraint.session is None


def test_label_fraction_initialization(label_fraction_constraint):
    """Make sure the correct fields go to the correct places."""
    assert label_fraction_constraint.formulation_descriptor == formulation_descriptor
    assert label_fraction_constraint.label == 'bar'
    assert label_fraction_constraint.min == 0.0
    assert label_fraction_constraint.max == 1.0
    assert not label_fraction_constraint.is_required
    assert label_fraction_constraint.session is None
