from uuid import UUID

import pytest

from citrine.resources.gem_resource import GemResourceCollection
from citrine.resources.material_run import MaterialRun
from tests.resources.test_data_concepts import run_noop_gemd_relation_search_test
from tests.utils.session import FakeSession


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def collection(session) -> GemResourceCollection:
    return GemResuorceCollection(
        project_id=UUID('6b608f78-e341-422c-8076-35adc8828545'),
        dataset_id=UUID('8da51e93-8b55-4dd3-8489-af8f65d4ad9a'),
        session=session)


def test_get(collection: GemResourceCollection):
    run_noop_gemd_relation_search_test(
        search_for='process-specs',
        search_with='process-templates',
        collection=collection,
        search_fn=collection.get,
    )


def test_list(collection: GemResourceCollection):
    run_noop_gemd_relation_search_test(
        search_for='process-specs',
        search_with='process-templates',
        collection=collection,
        search_fn=collection.list,
    )

def test_list_by_name(collection: GemResourceCollection):
    run_noop_gemd_relation_search_test(
        search_for='process-specs',
        search_with='process-templates',
        collection=collection,
        search_fn=collection.list_by_name,
    )


def test_list_by_tag(collection: GemResourceCollection):
    run_noop_gemd_relation_search_test(
        search_for='process-specs',
        search_with='process-templates',
        collection=collection,
        search_fn=collection.list_by_tag,
    )


def test_update(collection):
    with pytest.raises(NotImplementedError):
        collection.delete(MaterialRun('foo'))


def test_delete(collection):
    with pytest.raises(NotImplementedError):
        collection.delete(MaterialRun('foo'))


def test_register(collection):
    with pytest.raises(NotImplementedError):
        collection.delete(MaterialRun('foo'))


def test_register_all(collection):
    with pytest.raises(NotImplementedError):
        collection.delete(MaterialRun('foo'))