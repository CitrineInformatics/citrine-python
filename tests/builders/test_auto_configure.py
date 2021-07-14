from uuid import uuid4, UUID
from typing import Iterator, Union
import pytest

from citrine.resources.project import Project
from citrine.resources.table_config import TableConfigCollection

from citrine.informatics.objectives import ScalarMaxObjective
from citrine.informatics.scores import LIScore

from citrine.builders import AutoConfigureMode
from citrine.builders.auto_configure import auto_configure_candidates


@pytest.fixture()
def fake_project():
    """Fake project that returns auto-configured assets."""

    class FakeTableConfigCollection(TableConfigCollection):
        def __init__(self):
            pass

        def default_for_material(self):
            pass

    class FakeProject(Project):
        def __init__(self):
            pass

        @property
        def table_configs(self):
            return FakeTableConfigCollection()

    return FakeProject()

def test_auto_configure_arguments(fake_project: Project):
    """Ensure it throws if passed incorrect arguments."""
    score = LIScore(objectives=[ScalarMaxObjective(descriptor_key='Test')], baselines=[0.0])

    # Need to pass one of (material, table, predictor)
    with pytest.raises(ValueError):
        auto_configure_candidates(
            project=fake_project,
            score=score,
            mode=AutoConfigureMode.PLAIN,
            material=None,
            table=None,
            predictor=None,
        )

    with pytest.raises(ValueError):

