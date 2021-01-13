"""Tests for citrine.informatics.constraints."""
import pytest

from citrine.informatics.constraints import Constraint, ScalarRangeConstraint, CategoricalConstraint


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


def test_categorical_dumps(categorical_constraint):
    """Ensure values are persisted through deser."""
    result = categorical_constraint.dump()
    assert result['type'] == 'AcceptableCategoriesConstraint'
    assert result['descriptor_key'] == 'x'
    assert result['acceptable_classes'] == ['y', 'z']


def test_get_categorical_type(categorical_constraint):
    result = categorical_constraint.dump()
    typ = Constraint.get_type(result)
    assert typ == CategoricalConstraint
