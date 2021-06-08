"""Tests for citrine.informatics.constraints."""
import pytest

from citrine.informatics.constraints import Constraint, ScalarRangeConstraint, \
    AcceptableCategoriesConstraint


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
def acceptable_categories_constraint() -> AcceptableCategoriesConstraint:
    """Build a CategoricalConstraint."""
    return AcceptableCategoriesConstraint(
        descriptor_key='x',
        acceptable_categories=['y', 'z']
    )


def test_scalar_range_dumps(scalar_range_constraint):
    """Ensure values are persisted through deser."""
    result = scalar_range_constraint.dump()
    assert result['type'] == 'ScalarRange'
    assert result['descriptor_key'] == 'z'
    assert result['min'] == 1.0
    assert result['max'] == 10.0
    assert not result['min_inclusive']
    assert result['max_inclusive']


def test_get_scalar_range_type(scalar_range_constraint):
    result = scalar_range_constraint.dump()
    typ = Constraint.get_type(result)
    assert typ == ScalarRangeConstraint


def test_categorical_dumps(acceptable_categories_constraint):
    """Ensure values are persisted through deser."""
    result = acceptable_categories_constraint.dump()
    assert result['type'] == 'AcceptableCategoriesConstraint'
    assert result['descriptor_key'] == 'x'
    assert result['acceptable_classes'] == ['y', 'z']


def test_get_categorical_type(acceptable_categories_constraint):
    result = acceptable_categories_constraint.dump()
    typ = Constraint.get_type(result)
    assert typ == AcceptableCategoriesConstraint
