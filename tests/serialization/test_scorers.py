"""Tests for citrine.informatics.scorers."""
import pytest

from citrine.informatics.objectives import ScalarMaxObjective
from citrine.informatics.scorers import Scorer, MEIScorer, MLIScorer


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
        baselines=[1.0]
    )


def test_mli_dumps(mli_scorer):
    """Ensure values are persisted through deser."""
    result = mli_scorer.dump()
    assert result["type"] == "MLI"
    assert result["name"] == "MLI(z)"
    assert result["description"] == "experimental design score for z"
    assert result["baselines"][0] == 10.0
    assert result["objectives"][0]["type"] == "ScalarMax"


def test_get_mli_type(mli_scorer):
    """Ensure correct type is returned."""
    typ = Scorer.get_type(mli_scorer.dump())
    assert typ == MLIScorer


def test_mei_dumps(mei_scorer):
    """Ensure values are persisted through deser."""
    result = mei_scorer.dump()
    assert result["type"] == "MEI"
    assert result["name"] == "MEI(x)"
    assert result["description"] == "experimental design score for x"
    assert result["baselines"][0] == 1.0
    assert result["objectives"][0]["type"] == "ScalarMax"


def test_get_mei_type(mei_scorer):
    """Ensure correct type is returned."""
    typ = Scorer.get_type(mei_scorer.dump())
    assert typ == MEIScorer
