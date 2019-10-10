"""Tests for citrine.informatics.scorers."""
import pytest

from citrine.informatics.constraints import ScalarRangeConstraint
from citrine.informatics.objectives import ScalarMaxObjective
from citrine.informatics.scorers import MLIScorer, MEIScorer


@pytest.fixture
def mli_scorer() -> MLIScorer:
    """Build an MLIScorer."""
    return MLIScorer(
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
def mei_scorer() -> MEIScorer:
    """Build an MEIScorer."""
    return MEIScorer(
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


def test_mli_initialization(mli_scorer):
    """Make sure the correct fields go to the correct places."""
    assert mli_scorer.name == 'MLI(z)'
    assert mli_scorer.description == 'experimental design score for z'
    assert isinstance(mli_scorer.objectives[0], ScalarMaxObjective)
    assert mli_scorer.objectives[0].descriptor_key == 'z'
    assert mli_scorer.baselines == [10.0]
    assert mli_scorer.constraints == []


def test_mei_initialization(mei_scorer):
    """Make sure the correct fields go to the correct places."""
    assert mei_scorer.name == 'MEI(x)'
    assert mei_scorer.description == 'experimental design score for x'
    assert mei_scorer.objectives[0].descriptor_key == 'x'
    assert mei_scorer.baselines == [1.0]
    assert isinstance(mei_scorer.constraints[0], ScalarRangeConstraint)
    assert mei_scorer.constraints[0].descriptor_key == 'y'
