import json
from uuid import UUID, uuid4

import pytest
import requests_mock
from mock import patch, call

from tests.utils.factories import GemTableDataFactory
from tests.utils.session import FakeSession

from citrine.resources.gemtables import GemTableCollection, GemTable
from citrine.resources.project import Project
from citrine.informatics.objectives import ScalarMaxObjective, ScalarMinObjective

from citrine.builders.scores import create_default_score


@pytest.fixture
def table_data() -> str:
    header = "x,y,z\n"
    row1 = "1.0,0.0,dog\n"
    row2 = "0.0,1.0,cat"
    return header + row1 + row2


@pytest.fixture
def table():
    url = "http://otherhost:4572/anywhere"
    return GemTable.build(
        GemTableDataFactory(signed_download_url=url, version=2)
    )


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def project(session, table_data):
    """Fake project for table collection"""
    class FakeGemTableCollection(GemTableCollection):
        def __init__(self):
            pass

        def read_to_memory(self, table: GemTable) -> str:
            return table_data

    class FakeProject(Project):
        def __init__(self):
            pass

        @property
        def tables(self) -> FakeGemTableCollection:
            return FakeGemTableCollection()

    return FakeProject()


def test_create_default_score(project, table):
    """Test reading a table to create a default score for some objectives."""
    o1 = ScalarMinObjective(descriptor_key="x")
    o2 = ScalarMaxObjective(descriptor_key="y")
    o3 = ScalarMaxObjective(descriptor_key="z")
    o4 = ScalarMaxObjective(descriptor_key="bad")

    s1 = create_default_score(objectives=o1, project=project, table=table)
    assert s1.baselines[0] == 0.0

    s2 = create_default_score(objectives=o2, project=project, table=table)
    assert s2.baselines[0] == 1.0

    s3 = create_default_score(objectives=[o1, o2], project=project, table=table)
    assert s3.baselines[0] == 0.0
    assert s3.baselines[1] == 1.0

    # Check errors for poor descriptor choices
    with pytest.raises(ValueError):
        # Non numeric data
        create_default_score(objectives=o3, project=project, table=table)

    with pytest.raises(ValueError):
        # Not found in header
        create_default_score(objectives=o4, project=project, table=table)
