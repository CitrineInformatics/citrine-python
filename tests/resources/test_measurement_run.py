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
        project_id=UUID('6b608f78-e341-422c-8076-35adc8828545'),
        dataset_id=UUID('8da51e93-8b55-4dd3-8489-af8f65d4ad9a'),
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
