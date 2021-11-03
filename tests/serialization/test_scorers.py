"""Tests for citrine.informatics.scores."""
from citrine.informatics.objectives import ScalarMaxObjective
from citrine.informatics.scores import Score, EIScore, LIScore

from tests.informatics.test_scores import li_score, ei_score


def test_li_dumps(li_score):
    """Ensure values are persisted through deser."""
    result = li_score.dump()
    assert result["type"] == li_score.typ
    assert result["baselines"] == li_score.baselines
    assert result["objectives"][0]["type"] == ScalarMaxObjective.typ


def test_get_li_type(li_score):
    """Ensure correct type is returned."""
    typ = Score.get_type(li_score.dump())
    assert typ == LIScore


def test_ei_dumps(ei_score):
    """Ensure values are persisted through deser."""
    result = ei_score.dump()
    assert result["type"] == ei_score.typ
    assert result["baselines"] == ei_score.baselines
    assert result["objectives"][0]["type"] == ScalarMaxObjective.typ


def test_get_ei_type(ei_score):
    """Ensure correct type is returned."""
    typ = Score.get_type(ei_score.dump())
    assert typ == EIScore
