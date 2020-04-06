from uuid import UUID

import pytest
from citrine.resources.material_spec import MaterialSpecCollection

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
    specs = [spec for spec in collection.filter_by_template(test_id)]

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method="GET",
        path="projects/{}/material-templates/{}/{}/material-specs".format(project_id, test_scope, test_id),
        params={"forward": True, "ascending": True, "per_page": 20}
    )
    assert session.last_call == expected_call
    assert specs == [collection.build(sample_spec)]


def test_repeat_serialization_taurus(collection, session):
    """
    When registering a Taurus object, no unexpected fields should be added.  This is not no fields
    at all, since a serialization will add an `auto` scoped uid
    """
    from taurus.entity.object.material_spec import MaterialSpec as TaurusMaterial
    from taurus.entity.object.process_spec import ProcessSpec as TaurusProcess
    # Given
    session.set_response(MaterialSpecDataFactory(name='Test taurus mutation'))
    proc = TaurusProcess(name='Test taurus mutation (process)', uids={'nomutate': 'process'})
    mat = TaurusMaterial(name='Test taurus mutation', uids={'nomutate': 'material'}, process=proc)

    # When
    collection.register(proc)
    session.set_response(MaterialSpecDataFactory(name='Test taurus mutation'))
    registered = collection.register(mat)  # This will serialize the linked process as a side effect

    # Then
    assert "<Material spec 'Test taurus mutation'>" == str(registered)
