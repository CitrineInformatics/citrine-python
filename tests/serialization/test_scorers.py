"""Tests for citrine.informatics.scores."""
import pytest

from citrine.informatics.objectives import ScalarMaxObjective
from citrine.informatics.scores import Score, EIScore, LIScore


@pytest.fixture
def li_score() -> LIScore:
    """Build an LIScore."""
    return LIScore(
        name="LI(z)",
        description="experimental design score for z",
        objectives=[
            ScalarMaxObjective(
                descriptor_key="z"
            )
        ],
        baselines=[10.0]
    )


@pytest.fixture
def ei_score() -> EIScore:
    """Build an EIScore."""
    return EIScore(
        name="EI(x)",
        description="experimental design score for x",
        objectives=[
            ScalarMaxObjective(
                descriptor_key="x"
            )
        ],
        baselines=[1.0]
    )


def test_li_dumps(li_score):
    """Ensure values are persisted through deser."""
    result = li_score.dump()
    assert result["type"] == "MLI"
    assert result["name"] == "LI(z)"
    assert result["description"] == "experimental design score for z"
    assert result["baselines"][0] == 10.0
    assert result["objectives"][0]["type"] == "ScalarMax"


def test_get_li_type(li_score):
    """Ensure correct type is returned."""
    typ = Score.get_type(li_score.dump())
    assert typ == LIScore


def test_ei_dumps(ei_score):
    """Ensure values are persisted through deser."""
    result = ei_score.dump()
    assert result["type"] == "MEI"
    assert result["name"] == "EI(x)"
    assert result["description"] == "experimental design score for x"
    assert result["baselines"][0] == 1.0
    assert result["objectives"][0]["type"] == "ScalarMax"


def test_get_ei_type(ei_score):
    """Ensure correct type is returned."""
    typ = Score.get_type(ei_score.dump())
    assert typ == EIScore
