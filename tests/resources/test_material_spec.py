from uuid import UUID

import pytest
from citrine.resources.material_spec import MaterialSpecCollection
from tests.resources.test_data_concepts import run_noop_gemd_relation_search_test

from tests.utils.factories import MaterialTemplateFactory, \
    MaterialSpecDataFactory
from tests.utils.session import FakeCall, FakeSession


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def collection(session) -> MaterialSpecCollection:
    return MaterialSpecCollection(
        project_id=UUID('6b608f78-e341-422c-8076-35adc8828545'),
        dataset_id=UUID('8da51e93-8b55-4dd3-8489-af8f65d4ad9a'),
        session=session)


def test_filter_by_template(collection, session):
    """
    Test that MaterialSpecCollection.filter_by_template() hits the expected endpoint
    """
    # Given
    project_id = '6b608f78-e341-422c-8076-35adc8828545'
    material_template = MaterialTemplateFactory()
    test_scope = 'id'
    test_id = material_template.uids[test_scope]
    sample_spec = MaterialSpecDataFactory(template=material_template)
    session.set_response({'contents': [sample_spec]})

    # When
    specs = [spec for spec in collection.filter_by_template(test_id, per_page=20)]

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method="GET",
        path="projects/{}/material-templates/{}/{}/material-specs".format(project_id, test_scope, test_id),
        # per_page will be ignored
        params={"dataset_id": str(collection.dataset_id), "forward": True, "ascending": True, "per_page": 100}
    )
    assert session.last_call == expected_call
    assert specs == [collection.build(sample_spec)]


def test_list_by_template(collection):
    run_noop_gemd_relation_search_test(
        search_for='material-specs',
        search_with='material-templates',
        collection=collection,
        search_fn=collection.list_by_template,
    )


def test_get_by_process(collection):
    run_noop_gemd_relation_search_test(
        search_for='material-specs',
        search_with='process-specs',
        collection=collection,
        search_fn=collection.get_by_process,
        per_page=1,
    )


def test_repeat_serialization_gemd(collection, session):
    """
    When registering a GEMD object, no unexpected fields should be added.  This is not no fields
    at all, since a serialization will add an `auto` scoped uid
    """
    from gemd.entity.object.material_spec import MaterialSpec as GEMDMaterial
    from gemd.entity.object.process_spec import ProcessSpec as GEMDProcess
    # Given
    session.set_response(MaterialSpecDataFactory(name='Test gemd mutation'))
    proc = GEMDProcess(name='Test gemd mutation (process)', uids={'nomutate': 'process'})
    mat = GEMDMaterial(name='Test gemd mutation', uids={'nomutate': 'material'}, process=proc)

    # When
    collection.register(proc)
    session.set_response(MaterialSpecDataFactory(name='Test gemd mutation'))
    registered = collection.register(mat)  # This will serialize the linked process as a side effect

    # Then
    assert "<Material spec 'Test gemd mutation'>" == str(registered)
