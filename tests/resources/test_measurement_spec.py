from uuid import UUID

import pytest
    
from gemd.entity.object import MeasurementSpec as GEMDMeasurementSpec

from citrine.resources.measurement_spec import MeasurementSpec as CitrineMeasurementSpec, MeasurementSpecCollection
from tests.resources.test_data_concepts import run_noop_gemd_relation_search_test
from tests.utils.session import FakeSession


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def collection(session) -> MeasurementSpecCollection:
    return MeasurementSpecCollection(
        dataset_id=UUID('8da51e93-8b55-4dd3-8489-af8f65d4ad9a'),
        team_id = UUID('6b608f78-e341-422c-8076-35adc8828000'),
        session=session)


def test_create_deprecated_collection(session):
    with pytest.deprecated_call():
        MeasurementSpecCollection(
            project_id=UUID('6b608f78-e341-422c-8076-35adc8828545'),
            dataset_id=UUID('8da51e93-8b55-4dd3-8489-af8f65d4ad9a'),
            team_id = UUID('6b608f78-e341-422c-8076-35adc8828000'),
            session=session)


def test_create_deprecated_collection(session):
    with pytest.deprecated_call():
        MeasurementSpecCollection(
            project_id=UUID('6b608f78-e341-422c-8076-35adc8828545'),
            dataset_id=UUID('8da51e93-8b55-4dd3-8489-af8f65d4ad9a'),
            team_id = UUID('6b608f78-e341-422c-8076-35adc8828000'),
            session=session)


def test_list_by_template(collection: MeasurementSpecCollection):
    run_noop_gemd_relation_search_test(
        search_for='measurement-specs',
        search_with='measurement-templates',
        collection=collection,
        search_fn=collection.list_by_template,
    )


def test_equals():
    """Test basic equality.  Complex relationships are tested in test_material_run.test_deep_equals()."""
    gemd_obj = GEMDMeasurementSpec(
        name="My Name",
        notes="I have notes",
        tags=["tag!"]
    )
    citrine_obj = CitrineMeasurementSpec(
        name="My Name",
        notes="I have notes",
        tags=["tag!"]
    )
    assert gemd_obj == citrine_obj, "GEMD/Citrine equivalence"
    citrine_obj.notes = "Something else"
    assert gemd_obj != citrine_obj, "GEMD/Citrine detects difference"
