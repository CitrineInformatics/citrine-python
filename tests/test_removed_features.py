"""Removed platform features must fail locally with the platform's own message."""

import re
import uuid

import pytest

from citrine.exceptions import CitrineException, FeatureRemovedError
from citrine.informatics.design_spaces import ProductDesignSpace
from citrine.informatics.design_spaces.sample_design_space import SampleDesignSpaceInput
from citrine.informatics.generative_design import (
    FingerprintType,
    GenerativeDesignInput,
    StructureExclusion,
)
from citrine.resources.project import Project
from tests.utils.session import FakeSession

GENERATIVE_DESIGN_REMOVED = "Generative design has been removed from the Citrine Platform."
SAMPLING_REMOVED = "Design space sampling has been removed from the Citrine Platform."


def raises_removed(message: str):
    return pytest.raises(FeatureRemovedError, match=f"^{re.escape(message)}$")


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def project(session) -> Project:
    project = Project(name="Removed features", session=session, team_id=uuid.uuid4())
    project.uid = uuid.uuid4()
    return project


@pytest.fixture
def design_space(session, project) -> ProductDesignSpace:
    design_space = ProductDesignSpace(name="Removed features", description="")
    design_space.uid = uuid.uuid4()
    design_space._project_id = project.uid
    design_space._session = session
    return design_space


def test_removal_error_is_a_citrine_exception():
    assert issubclass(FeatureRemovedError, CitrineException)


def test_generative_design_script_fails_at_the_input(session):
    with raises_removed(GENERATIVE_DESIGN_REMOVED):
        GenerativeDesignInput(
            seeds=["C"],
            fingerprint_type=FingerprintType.ECFP4,
            min_fingerprint_similarity=0.1,
            mutation_per_seed=25,
            structure_exclusions=[StructureExclusion.IONS],
        )
    assert session.num_calls == 0


def test_generative_design_executions_raise(project, session):
    with raises_removed(GENERATIVE_DESIGN_REMOVED):
        project.generative_design_executions.list()
    assert session.num_calls == 0


def test_sampling_script_fails_at_the_input(session):
    with raises_removed(SAMPLING_REMOVED):
        SampleDesignSpaceInput(n_candidates=50)
    assert session.num_calls == 0


def test_sample_design_space_executions_raise(design_space, session):
    with raises_removed(SAMPLING_REMOVED):
        design_space.sample_design_space_executions.trigger(None)
    assert session.num_calls == 0


def test_removed_accessors_are_absent_to_introspection(project, design_space, session):
    assert not hasattr(project, "generative_design_executions")
    assert not hasattr(design_space, "sample_design_space_executions")
    assert session.num_calls == 0
