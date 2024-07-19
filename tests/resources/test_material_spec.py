from uuid import UUID

import pytest

from citrine.resources.material_spec import MaterialSpec as CitrineMaterialSpec, MaterialSpecCollection
from tests.resources.test_data_concepts import run_noop_gemd_relation_search_test
from tests.utils.factories import MaterialSpecDataFactory
from tests.utils.session import FakeCall, FakeSession

from gemd.entity.object import MaterialSpec as GEMDMaterialSpec


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def collection(session) -> MaterialSpecCollection:
    return MaterialSpecCollection(
        dataset_id=UUID('8da51e93-8b55-4dd3-8489-af8f65d4ad9a'),
        team_id = UUID('6b608f78-e341-422c-8076-35adc8828000'),
        session=session)


def test_create_deprecated_collection(session):
    project_id = '6b608f78-e341-422c-8076-35adc8828545'
    session.set_response({'project': {'team': {'id': UUID("6b608f78-e341-422c-8076-35adc8828000")}}})

    with pytest.deprecated_call():
        MaterialSpecCollection(
            project_id=UUID(project_id),
            dataset_id=UUID('8da51e93-8b55-4dd3-8489-af8f65d4ad9a'),
            session=session)

    assert session.calls == [FakeCall(method="GET", path=f'projects/{project_id}')]


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


def test_equals():
    gemd_obj = GEMDMaterialSpec(
        name="My Name",
        notes="I have notes",
        tags=["tag!"]
    )
    citrine_obj = CitrineMaterialSpec(
        name="My Name",
        notes="I have notes",
        tags=["tag!"]
    )
    assert gemd_obj == citrine_obj, "GEMD/Citrine equivalence"
    citrine_obj.notes = "Something else"
    assert gemd_obj != citrine_obj, "GEMD/Citrine detects difference"
