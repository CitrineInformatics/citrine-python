"""Tests for citrine.informatics.scores."""
import pytest

from citrine.informatics.objectives import ScalarMaxObjective
from citrine.informatics.scores import Score, MEIScore, MLIScore


@pytest.fixture
def mli_score() -> MLIScore:
    """Build an MLIScore."""
    return MLIScore(
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
def mei_score() -> MEIScore:
    """Build an MEIScore."""
    return MEIScore(
        name="MEI(x)",
        description="experimental design score for x",
        objectives=[
            ScalarMaxObjective(
                descriptor_key="x"
            )
        ],
        baselines=[1.0]
    )


def test_mli_dumps(mli_score):
    """Ensure values are persisted through deser."""
    result = mli_score.dump()
    assert result["type"] == "MLI"
    assert result["name"] == "MLI(z)"
    assert result["description"] == "experimental design score for z"
    assert result["baselines"][0] == 10.0
    assert result["objectives"][0]["type"] == "ScalarMax"


def test_get_mli_type(mli_score):
    """Ensure correct type is returned."""
    typ = Score.get_type(mli_score.dump())
    assert typ == MLIScore


def test_mei_dumps(mei_score):
    """Ensure values are persisted through deser."""
    result = mei_score.dump()
    assert result["type"] == "MEI"
    assert result["name"] == "MEI(x)"
    assert result["description"] == "experimental design score for x"
    assert result["baselines"][0] == 1.0
    assert result["objectives"][0]["type"] == "ScalarMax"


def test_get_mei_type(mei_score):
    """Ensure correct type is returned."""
    typ = Score.get_type(mei_score.dump())
    assert typ == MEIScore
