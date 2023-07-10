"""Tests for citrine.informatics.constraints."""
import pytest

from citrine.informatics.constraints import *
from citrine.informatics.descriptors import FormulationDescriptor

formulation_descriptor = FormulationDescriptor.hierarchical()


@pytest.fixture
def scalar_range_constraint() -> ScalarRangeConstraint:
    """Build a ScalarRangeConstraint."""
    return ScalarRangeConstraint(
        descriptor_key='z',
        lower_bound=1.0,
        upper_bound=10.0,
        lower_inclusive=False
    )


@pytest.fixture
def integer_range_constraint() -> IntegerRangeConstraint:
    """Build an IntegerRangeConstraint."""
    return IntegerRangeConstraint(
        descriptor_key='integer',
        lower_bound=1,
        upper_bound=10,
        lower_inclusive=False
    )


@pytest.fixture
def categorical_constraint() -> AcceptableCategoriesConstraint:
    """Build a CategoricalConstraint."""
    return AcceptableCategoriesConstraint(
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


@pytest.fixture
def ingredient_ratio_constraint() -> IngredientRatioConstraint:
    """Build an IngredientRatioConstraint"""
    return IngredientRatioConstraint(
        formulation_descriptor=formulation_descriptor,
        min=0.0,
        max=1e6,
        ingredient=("foo", 1.0),
        label=("foolabel", 0.5),
        basis_ingredients=["baz", "bat"],
        basis_labels=["bazlabel", "batlabel"]
    )


def test_scalar_range_initialization(scalar_range_constraint):
    """Make sure the correct fields go to the correct places."""
    assert scalar_range_constraint.descriptor_key == 'z'
    assert scalar_range_constraint.lower_bound == 1.0
    assert scalar_range_constraint.upper_bound == 10.0
    assert not scalar_range_constraint.lower_inclusive
    assert scalar_range_constraint.upper_inclusive


def test_integer_range_initialization(integer_range_constraint):
    """Make sure the correct fields go to the correct places."""
    assert integer_range_constraint.descriptor_key == 'integer'
    assert integer_range_constraint.lower_bound == 1
    assert integer_range_constraint.upper_bound == 10
    assert not integer_range_constraint.lower_inclusive
    assert not integer_range_constraint.upper_inclusive


def test_categorical_initialization(categorical_constraint):
    """Make sure the correct fields go to the correct places."""
    assert categorical_constraint.descriptor_key == 'x'
    assert categorical_constraint.acceptable_categories == ['y', 'z']
    assert "Acceptable" in str(categorical_constraint)


def test_ingredient_fraction_initialization(ingredient_fraction_constraint):
    """Make sure the correct fields go to the correct places."""
    assert ingredient_fraction_constraint.formulation_descriptor == formulation_descriptor
    assert ingredient_fraction_constraint.ingredient == 'foo'
    assert ingredient_fraction_constraint.min == 0.0
    assert ingredient_fraction_constraint.max == 1.0
    assert not ingredient_fraction_constraint.is_required


def test_ingredient_count_initialization(ingredient_count_constraint):
    """Make sure the correct fields go to the correct places."""
    assert ingredient_count_constraint.formulation_descriptor == formulation_descriptor
    assert ingredient_count_constraint.min == 0
    assert ingredient_count_constraint.max == 1
    assert ingredient_count_constraint.label == 'bar'


def test_label_fraction_initialization(label_fraction_constraint):
    """Make sure the correct fields go to the correct places."""
    assert label_fraction_constraint.formulation_descriptor == formulation_descriptor
    assert label_fraction_constraint.label == 'bar'
    assert label_fraction_constraint.min == 0.0
    assert label_fraction_constraint.max == 1.0
    assert not label_fraction_constraint.is_required


def test_ingredient_ratio_initialization(ingredient_ratio_constraint):
    """Make sure the correct fields go to the correct places."""
    assert ingredient_ratio_constraint.formulation_descriptor == formulation_descriptor
    assert ingredient_ratio_constraint.min == 0.0
    assert ingredient_ratio_constraint.max == 1e6
    assert ingredient_ratio_constraint.ingredient == ("foo", 1.0)
    assert ingredient_ratio_constraint.label == ("foolabel", 0.5)
    assert ingredient_ratio_constraint.basis_ingredient_names == {"baz", "bat"}
    assert ingredient_ratio_constraint.basis_label_names == {"bazlabel", "batlabel"}


def test_ingredient_ratio_interaction(ingredient_ratio_constraint):
    with pytest.raises(ValueError):
        ingredient_ratio_constraint.ingredient = ("foo", 2, "bar", 4)
    with pytest.raises(ValueError):
        ingredient_ratio_constraint.ingredient = ("foo", )
    with pytest.raises(TypeError):
        ingredient_ratio_constraint.ingredient = ("foo", "yup")
    with pytest.raises(ValueError):
        ingredient_ratio_constraint.ingredient = ("foo", -1)

    newval = ("foo", 42)
    ingredient_ratio_constraint.ingredient = newval
    assert ingredient_ratio_constraint.ingredient == newval
    ingredient_ratio_constraint.ingredient = None
    assert ingredient_ratio_constraint.ingredient is None
    ingredient_ratio_constraint.ingredient = []
    assert ingredient_ratio_constraint.ingredient is None

    with pytest.raises(ValueError):
        ingredient_ratio_constraint.label = ("foolabel", 2, "barlabel", 4)
    with pytest.raises(ValueError):
        ingredient_ratio_constraint.label = ("foolabel", )
    with pytest.raises(TypeError):
        ingredient_ratio_constraint.label = ("foolabel", "yup")
    with pytest.raises(ValueError):
        ingredient_ratio_constraint.label = ("foolabel", -1)

    newval = ("foolabel", 42)
    ingredient_ratio_constraint.label = newval
    assert ingredient_ratio_constraint.label == newval
    ingredient_ratio_constraint.label = None
    assert ingredient_ratio_constraint.label is None
    ingredient_ratio_constraint.label = []
    assert ingredient_ratio_constraint.label is None

    newval_dict = {"foobasis": 3}
    with pytest.deprecated_call():
        ingredient_ratio_constraint.basis_ingredients = newval_dict
    with pytest.deprecated_call():
        assert ingredient_ratio_constraint.basis_ingredients == dict.fromkeys(newval_dict.keys(), 1)
    ingredient_ratio_constraint.basis_ingredient_names = set(newval_dict.keys())

    newval_set = {"foobasis2"}
    ingredient_ratio_constraint.basis_ingredients = newval_set
    with pytest.deprecated_call():
        assert ingredient_ratio_constraint.basis_ingredients == dict.fromkeys(newval_set, 1)
    ingredient_ratio_constraint.basis_ingredient_names = newval_set

    newval_set = {"foobasis3"}
    ingredient_ratio_constraint.basis_ingredient_names = newval_set
    with pytest.deprecated_call():
        assert ingredient_ratio_constraint.basis_ingredients == dict.fromkeys(newval_set, 1)
    ingredient_ratio_constraint.basis_ingredient_names = newval_set

    newval_dict = {"foolabelbasis": 3}
    with pytest.deprecated_call():
        ingredient_ratio_constraint.basis_labels = newval_dict
    with pytest.deprecated_call():
        assert ingredient_ratio_constraint.basis_labels == dict.fromkeys(newval_dict.keys(), 1)
    ingredient_ratio_constraint.basis_label_names = set(newval_dict.keys())

    newval_set = {"foolabelbasis2"}
    ingredient_ratio_constraint.basis_labels = newval_set
    with pytest.deprecated_call():
        assert ingredient_ratio_constraint.basis_labels == dict.fromkeys(newval_set, 1)
    ingredient_ratio_constraint.basis_label_names = newval_set

    newval_set = {"foolabelbasis3"}
    ingredient_ratio_constraint.basis_label_names = newval_set
    with pytest.deprecated_call():
        assert ingredient_ratio_constraint.basis_labels == dict.fromkeys(newval_set, 1)
    ingredient_ratio_constraint.basis_label_names = newval_set


def test_range_defaults():
    """Check that deprecated and default values work as expected."""
    assert ScalarRangeConstraint(descriptor_key="x").lower_bound is None
    assert ScalarRangeConstraint(descriptor_key="x").upper_bound is None
    assert ScalarRangeConstraint(descriptor_key="x").lower_inclusive is True
    assert ScalarRangeConstraint(descriptor_key="x").upper_inclusive is True

    assert ScalarRangeConstraint(descriptor_key="x", upper_inclusive=False).upper_inclusive is False
    assert ScalarRangeConstraint(descriptor_key="x", lower_inclusive=False).lower_inclusive is False

    assert ScalarRangeConstraint(descriptor_key="x", lower_bound=0).lower_bound == 0.0
    assert ScalarRangeConstraint(descriptor_key="x", upper_bound=0).upper_bound == 0.0
