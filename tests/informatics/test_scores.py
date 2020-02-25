"""Tests for citrine.informatics.scores."""
import pytest

from citrine.informatics.constraints import ScalarRangeConstraint
from citrine.informatics.objectives import ScalarMaxObjective
from citrine.informatics.scores import LIScore, EIScore


@pytest.fixture
def mli_score() -> LIScore:
    """Build an MLIScore."""
    return LIScore(
        name="MLI(z)",
        description="experimental design score for z",
        objectives=[
            ScalarMaxObjective(
                descriptor_key="z"
            )
        ],
        baselines=[10.0]
    )


@pytest.fixture
def mei_score() -> EIScore:
    """Build an MEIScore."""
    return EIScore(
        name="MEI(x)",
        description="experimental design score for x",
        objectives=[
            ScalarMaxObjective(
                descriptor_key="x"
            )
        ],
        baselines=[1.0],
        constraints=[ScalarRangeConstraint('y', 0.0, 1.0)]
    )


def test_mli_initialization(mli_score):
    """Make sure the correct fields go to the correct places."""
    assert mli_score.name == 'MLI(z)'
    assert mli_score.description == 'experimental design score for z'
    assert isinstance(mli_score.objectives[0], ScalarMaxObjective)
    assert mli_score.objectives[0].descriptor_key == 'z'
    assert mli_score.baselines == [10.0]
    assert mli_score.constraints == []


def test_mei_initialization(mei_score):
    """Make sure the correct fields go to the correct places."""
    assert mei_score.name == 'MEI(x)'
    assert mei_score.description == 'experimental design score for x'
    assert mei_score.objectives[0].descriptor_key == 'x'
    assert mei_score.baselines == [1.0]
    assert isinstance(mei_score.constraints[0], ScalarRangeConstraint)
    assert mei_score.constraints[0].descriptor_key == 'y'
