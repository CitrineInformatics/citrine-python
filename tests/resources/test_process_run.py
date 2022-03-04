from uuid import UUID

import pytest

from citrine.resources.process_run import ProcessRunCollection
from tests.resources.test_data_concepts import run_noop_gemd_relation_search_test
from tests.utils.session import FakeSession


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def collection(session) -> ProcessRunCollection:
    return ProcessRunCollection(
        project_id=UUID('6b608f78-e341-422c-8076-35adc8828545'),
        dataset_id=UUID('8da51e93-8b55-4dd3-8489-af8f65d4ad9a'),
        session=session)


def test_list_by_spec(collection: ProcessRunCollection):
    run_noop_gemd_relation_search_test(
        search_for='process-runs',
        search_with='process-specs',
        collection=collection,
        search_fn=collection.list_by_spec,
    )


def test_equals():
    """Test basic equality.  Complex relationships are tested in test_material_run.test_deep_equals()."""
    from citrine.resources.process_run import ProcessRun as CitrineProcessRun
    from gemd.entity.object import ProcessRun as GEMDProcessRun

    gemd_obj = GEMDProcessRun(
        name="My Name",
        notes="I have notes",
        tags=["tag!"]
    )
    citrine_obj = CitrineProcessRun(
        name="My Name",
        notes="I have notes",
        tags=["tag!"]
    )
    assert gemd_obj == citrine_obj, "GEMD/Citrine equivalence"
    citrine_obj.notes = "Something else"
    assert gemd_obj != citrine_obj, "GEMD/Citrine detects difference"
