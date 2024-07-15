from uuid import UUID

import pytest

from citrine.resources.measurement_run import MeasurementRunCollection
from tests.resources.test_data_concepts import run_noop_gemd_relation_search_test
from tests.utils.session import FakeSession


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def collection(session) -> MeasurementRunCollection:
    return MeasurementRunCollection(
        dataset_id=UUID('8da51e93-8b55-4dd3-8489-af8f65d4ad9a'),
        team_id = UUID('6b608f78-e341-422c-8076-35adc8828000'),
        session=session)


def test_create_deprecated_collection(session):
    with pytest.deprecated_call():
        MeasurementRunCollection(
            project_id=UUID('6b608f78-e341-422c-8076-35adc8828545'),
            dataset_id=UUID('8da51e93-8b55-4dd3-8489-af8f65d4ad9a'),
            team_id = UUID('6b608f78-e341-422c-8076-35adc8828000'),
            session=session)


def test_list_by_template(collection: MeasurementRunCollection):
    run_noop_gemd_relation_search_test(
        search_for='measurement-runs',
        search_with='measurement-specs',
        collection=collection,
        search_fn=collection.list_by_spec,
    )


def test_list_by_material(collection: MeasurementRunCollection):
    run_noop_gemd_relation_search_test(
        search_for='measurement-runs',
        search_with='material-runs',
        collection=collection,
        search_fn=collection.list_by_material,
    )


def test_equals():
    """Test basic equality.  Complex relationships are tested in test_material_run.test_deep_equals()."""
    from citrine.resources.measurement_run import MeasurementRun as CitrineMeasurementRun
    from gemd.entity.object import MeasurementRun as GEMDMeasurementRun

    gemd_obj = GEMDMeasurementRun(
        name="My Name",
        notes="I have notes",
        tags=["tag!"]
    )
    citrine_obj = CitrineMeasurementRun(
        name="My Name",
        notes="I have notes",
        tags=["tag!"]
    )
    assert gemd_obj == citrine_obj, "GEMD/Citrine equivalence"
    citrine_obj.notes = "Something else"
    assert gemd_obj != citrine_obj, "GEMD/Citrine detects difference"
