"""Tests for citrine.informatics.objectives."""
import pytest

from citrine.informatics.objectives import Objective, ScalarMaxObjective, ScalarMinObjective


@pytest.fixture
def scalar_max_objective() -> ScalarMaxObjective:
    """Build a ScalarMaxObjective."""
    return ScalarMaxObjective(
        descriptor_key="z"
    )


@pytest.fixture
def scalar_min_objective() -> ScalarMinObjective:
    """Build a ScalarMinObjective."""
    return ScalarMinObjective(
        descriptor_key="z"
    )


def test_scalar_max_dumps(scalar_max_objective):
    """Ensure values are persisted through deser."""
    result = scalar_max_objective.dump()
    assert result["type"] == "ScalarMax"
    assert result["descriptor_key"] == "z"


def test_get_scalar_max_type(scalar_max_objective):
    result = scalar_max_objective.dump()
    typ = Objective.get_type(result)
    assert typ == ScalarMaxObjective


def test_scalar_min_dumps(scalar_min_objective):
    """Ensure values are persisted through deser."""
    result = scalar_min_objective.dump()
    assert result["type"] == "ScalarMin"
    assert result["descriptor_key"] == "z"


def test_get_scalar_min_type(scalar_min_objective):
    result = scalar_min_objective.dump()
    typ = Objective.get_type(result)
    assert typ == ScalarMinObjective
