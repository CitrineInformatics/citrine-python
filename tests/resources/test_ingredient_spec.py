from uuid import UUID

import pytest

from citrine.resources.ingredient_spec import IngredientSpecCollection
from tests.resources.test_data_concepts import run_noop_gemd_relation_search_test
from tests.utils.session import FakeSession


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def collection(session) -> IngredientSpecCollection:
    return IngredientSpecCollection(
        project_id=UUID('6b608f78-e341-422c-8076-35adc8828545'),
        dataset_id=UUID('8da51e93-8b55-4dd3-8489-af8f65d4ad9a'),
        session=session)


def test_list_by_material(collection: IngredientSpecCollection):
    run_noop_gemd_relation_search_test(
        search_for='ingredient-specs',
        search_with='material-specs',
        collection=collection,
        search_fn=collection.list_by_material,
    )


def test_list_by_process(collection: IngredientSpecCollection):
    run_noop_gemd_relation_search_test(
        search_for='ingredient-specs',
        search_with='process-specs',
        collection=collection,
        search_fn=collection.list_by_process,
    )
