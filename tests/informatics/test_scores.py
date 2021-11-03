"""Tests for citrine.informatics.scores."""
import pytest

from citrine.informatics.constraints import ScalarRangeConstraint
from citrine.informatics.objectives import ScalarMaxObjective
from citrine.informatics.scores import LIScore, EIScore, EVScore


@pytest.fixture
def li_score() -> LIScore:
    """Build an LIScore."""
    return LIScore(
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
        objectives=[
            ScalarMaxObjective(
                descriptor_key="x"
            )
        ],
        baselines=[1.0],
        constraints=[ScalarRangeConstraint(descriptor_key='y', lower_bound=0.0, upper_bound=1.0)]
    )


@pytest.fixture
def ev_score() -> EVScore:
    """Build an MEVScore."""
    return EVScore(
        objectives=[
            ScalarMaxObjective(
                descriptor_key="x"
            )
        ],
        constraints=[ScalarRangeConstraint(descriptor_key='y', lower_bound=0.0, upper_bound=1.0)]
    )


def test_li_initialization(li_score):
    """Make sure the correct fields go to the correct places."""
    assert isinstance(li_score.objectives[0], ScalarMaxObjective)
    assert li_score.objectives[0].descriptor_key == 'z'
    assert li_score.baselines == [10.0]
    assert li_score.constraints == []


def test_ei_initialization(ei_score):
    """Make sure the correct fields go to the correct places."""
    assert ei_score.objectives[0].descriptor_key == 'x'
    assert ei_score.baselines == [1.0]
    assert isinstance(ei_score.constraints[0], ScalarRangeConstraint)
    assert ei_score.constraints[0].descriptor_key == 'y'


def test_ev_initialization(ev_score):
    """Make sure the correct fields go to the correct places."""
    assert ev_score.objectives[0].descriptor_key == 'x'
    assert isinstance(ev_score.constraints[0], ScalarRangeConstraint)
    assert ev_score.constraints[0].descriptor_key == 'y'
    assert "EVScore" in str(ev_score)


def test_deprecated_score_fields():
    """Build an LIScore."""
    with pytest.warns(DeprecationWarning):
        li_score = LIScore(
            name="LI(z)",
            description="experimental design score for z",
            objectives=[
                ScalarMaxObjective(
                    descriptor_key="z"
                )
            ],
            baselines=[10.0]
        )
    with pytest.warns(DeprecationWarning):
        assert li_score.name == 'LI(z)'
    with pytest.warns(DeprecationWarning):
        assert li_score.description == 'experimental design score for z'

    """Build an EIScore."""
    with pytest.warns(DeprecationWarning):
        ei_score = EIScore(
            name="EI(x)",
            description="experimental design score for x",
            objectives=[
                ScalarMaxObjective(
                    descriptor_key="x"
                )
            ],
            baselines=[1.0],
            constraints=[ScalarRangeConstraint(descriptor_key='y', lower_bound=0.0, upper_bound=1.0)]
        )
    with pytest.warns(DeprecationWarning):
        assert ei_score.name == 'EI(x)'
    with pytest.warns(DeprecationWarning):
        assert ei_score.description == 'experimental design score for x'

    """Build an MEVScore."""
    with pytest.warns(DeprecationWarning):
        ev_score = EVScore(
            name="EV(x)",
            description="experimental design score for x",
            objectives=[
                ScalarMaxObjective(
                    descriptor_key="x"
                )
            ],
            constraints=[ScalarRangeConstraint(descriptor_key='y', lower_bound=0.0, upper_bound=1.0)]
        )
    with pytest.warns(DeprecationWarning):
        assert ev_score.name == 'EV(x)'
    with pytest.warns(DeprecationWarning):
        assert ev_score.description == 'experimental design score for x'
