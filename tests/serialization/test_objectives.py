"""Tests for citrine.informatics.objectives."""
import pytest

from citrine.informatics.objectives import ScalarMaxObjective


@pytest.fixture
def objective() -> ScalarMaxObjective:
    """Build a ScalarMaxObjective."""
    return ScalarMaxObjective(
        descriptor_key="z",
        lower_bound=1.0,
        upper_bound=10.0
    )


@pytest.fixture
def objective_no_limits() -> ScalarMaxObjective:
    """Build a ScalarMaxObjective."""
    return ScalarMaxObjective(
        descriptor_key="z"
    )


def test_dumps(objective: ScalarMaxObjective):
    """Ensure values are persisted through deser."""
    result = objective.dump()
    assert result["type"] == "ScalarMax"
    assert result["descriptor_key"] == "z"


def test_dumps_no_limits(objective_no_limits: ScalarMaxObjective):
    """Ensure defaults are None."""
    result = objective_no_limits.dump()
    assert result["type"] == "ScalarMax"
    assert result["descriptor_key"] == "z"
    assert result["lower_bound"] is None
    assert result["upper_bound"] is None
