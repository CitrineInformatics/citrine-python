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


def test_initialization(objective: ScalarMaxObjective):
    """Make sure the correct fields go to the correct places."""
    assert objective.descriptor_key == "z"
    assert objective.lower_bound == 1.0
    assert objective.upper_bound == 10.0
