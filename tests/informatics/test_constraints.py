"""Tests for citrine.informatics.constraints."""
import pytest

from citrine.informatics.constraints import ScalarRangeConstraint, CategoricalConstraint


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


def test_scalar_range_repr(scalar_range_constraint):
    assert str(scalar_range_constraint) == "<ScalarRangeConstraint 'z'>"


def test_categorical_repr(categorical_constraint):
    assert str(categorical_constraint) == "<CategoricalConstraint 'x'>"


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
