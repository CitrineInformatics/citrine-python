"""Tests for citrine.informatics.objectives."""
import pytest

from citrine.informatics.objectives import ScalarMaxObjective, ScalarMinObjective


@pytest.fixture
def scalar_max_objective() -> ScalarMaxObjective:
    """Build a ScalarMaxObjective."""
    return ScalarMaxObjective(
        descriptor_key="z",
        lower_bound=1.0,
        upper_bound=10.0
    )


@pytest.fixture
def scalar_min_objective() -> ScalarMinObjective:
    """Build a ScalarMinObjective."""
    return ScalarMinObjective(
        descriptor_key="z",
        lower_bound=1.0,
        upper_bound=10.0
    )


def test_max_objective_repr(scalar_max_objective):
    assert str(scalar_max_objective) == "<ScalarMaxObjective 'z'>"


def test_min_objective_repr(scalar_min_objective):
    assert str(scalar_min_objective) == "<ScalarMinObjective 'z'>"


def test_scalar_max_initialization(scalar_max_objective):
    """Make sure the correct fields go to the correct places."""
    assert scalar_max_objective.descriptor_key == "z"
    assert scalar_max_objective.lower_bound == 1.0
    assert scalar_max_objective.upper_bound == 10.0


def test_scalar_min_initialization(scalar_min_objective):
    """Make sure the correct fields go to the correct places."""
    assert scalar_min_objective.descriptor_key == "z"
    assert scalar_min_objective.lower_bound == 1.0
    assert scalar_min_objective.upper_bound == 10.0
