"""Tests for citrine.informatics.scorers."""
import pytest

from citrine.informatics.objectives import ScalarMaxObjective
from citrine.informatics.scorers import MLIScorer


@pytest.fixture
def scorer() -> MLIScorer:
    """Build a MLIScorer."""
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


def test_dumps(scorer: MLIScorer):
    """Ensure values are persisted through deser."""
    result = scorer.dump()
    assert result["type"] == "MLI"
    assert result["name"] == "MLI(z)"
    assert result["description"] == "experimental design score for z"
    assert result["baselines"][0] == 10.0
    assert result["objectives"][0]["type"] == "ScalarMax"
