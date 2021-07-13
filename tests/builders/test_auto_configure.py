from uuid import uuid4, UUID
from typing import Iterator, Union
import pytest

from citrine.resources.project import Project
from citrine.resources.table_config import TableConfigCollection

from citrine.builders import AutoConfigureMode
@pytest.fixture()
def fake_project():
    """Fake project that returns auto-configured assets."""

    class FakeTableConfigCollection(TableConfigCollection):
        def __init__(self):
            pass

        def default_for_material

    class FakeProject(Project):
        def __init__(self):
            pass

        @property
        def table_configs(self):
            return FakeTableConfigCollection()

    return FakeProject()