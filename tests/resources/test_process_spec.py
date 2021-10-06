from uuid import UUID

import pytest

from citrine.resources.process_spec import ProcessSpecCollection
from tests.resources.test_data_concepts import run_noop_gemd_relation_search_test
from tests.utils.session import FakeSession


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def collection(session) -> ProcessSpecCollection:
    return ProcessSpecCollection(
        project_id=UUID('6b608f78-e341-422c-8076-35adc8828545'),
        dataset_id=UUID('8da51e93-8b55-4dd3-8489-af8f65d4ad9a'),
        session=session)


def test_list_by_template(collection: ProcessSpecCollection):
    run_noop_gemd_relation_search_test(
        search_for='process-specs',
        search_with='process-templates',
        collection=collection,
        search_fn=collection.list_by_template,
    )


def test_equals():
    """Test basic equality.  Complex relationships are tested in test_material_run.test_deep_equals()."""
    from citrine.resources.process_spec import ProcessSpec as CitrineProcesssSpec
    from gemd.entity.object import ProcessSpec as GEMDProcessSpec

    gemd_obj = GEMDProcessSpec(
        name="My Name",
        notes="I have notes",
        tags=["tag!"]
    )
    citrine_obj = CitrineProcesssSpec(
        name="My Name",
        notes="I have notes",
        tags=["tag!"]
    )
    assert gemd_obj == citrine_obj, "GEMD/Citrine equivalence"
    citrine_obj.notes = "Something else"
    assert gemd_obj != citrine_obj, "GEMD/Citrine detects difference"
