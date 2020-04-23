from uuid import UUID

import pytest

from citrine.resources.ingredient_run import IngredientRunCollection
from tests.resources.test_data_concepts import run_noop_gemd_relation_search_test
from tests.utils.session import FakeSession


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def collection(session) -> IngredientRunCollection:
    return IngredientRunCollection(
        project_id=UUID('6b608f78-e341-422c-8076-35adc8828545'),
        dataset_id=UUID('8da51e93-8b55-4dd3-8489-af8f65d4ad9a'),
        session=session)


def test_list_by_spec(collection: IngredientRunCollection):
    run_noop_gemd_relation_search_test(
        search_for='ingredient-runs',
        search_with='ingredient-specs',
        collection=collection,
        search_fn=collection.list_by_spec,
    )


def test_list_by_material(collection: IngredientRunCollection):
    run_noop_gemd_relation_search_test(
        search_for='ingredient-runs',
        search_with='material-runs',
        collection=collection,
        search_fn=collection.list_by_material,
    )


def test_list_by_process(collection: IngredientRunCollection):
    run_noop_gemd_relation_search_test(
        search_for='ingredient-runs',
        search_with='process-runs',
        collection=collection,
        search_fn=collection.list_by_process,
    )
