"""Tests for citrine.informatics.objectives."""
import pytest

from citrine.informatics.objectives import ScalarMaxObjective, ScalarMinObjective


@pytest.fixture
def scalar_max_objective() -> ScalarMaxObjective:
    """Build a ScalarMaxObjective."""
    return ScalarMaxObjective(
        descriptor_key="z",
    )


@pytest.fixture
def scalar_min_objective() -> ScalarMinObjective:
    """Build a ScalarMinObjective."""
    return ScalarMinObjective(
        descriptor_key="z",
    )


def test_scalar_max_initialization(scalar_max_objective):
    """Make sure the correct fields go to the correct places."""
    assert scalar_max_objective.descriptor_key == "z"


def test_scalar_min_initialization(scalar_min_objective):
    """Make sure the correct fields go to the correct places."""
    assert scalar_min_objective.descriptor_key == "z"
