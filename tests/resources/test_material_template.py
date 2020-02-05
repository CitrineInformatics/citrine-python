from uuid import UUID

import pytest
from citrine.resources.material_spec import MaterialSpecCollection
from citrine.resources.material_template import MaterialTemplateCollection

from tests.utils.factories import MaterialTemplateFactory, MaterialSpecDataFactory, MaterialRunDataFactory
from tests.utils.session import FakeSession, FakeCall


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def collection(session) -> MaterialTemplateCollection:
    return MaterialTemplateCollection(
        project_id=UUID('6b608f78-e341-422c-8076-35adc8828545'),
        dataset_id=UUID('8da51e93-8b55-4dd3-8489-af8f65d4ad9a'),
        session=session)


@pytest.fixture
def spec_collection(session) -> MaterialSpecCollection:
    return MaterialSpecCollection(
        project_id=UUID('6b608f78-e341-422c-8076-35adc8828545'),
        dataset_id=UUID('8da51e93-8b55-4dd3-8489-af8f65d4ad9a'),
        session=session)


def test_get_specs(collection, session):
    # Given
    project_id = '6b608f78-e341-422c-8076-35adc8828545'
    material_template = MaterialTemplateFactory()
    test_scope = 'id'
    test_id = material_template.uids[test_scope]
    sample_spec = MaterialSpecDataFactory(template=test_id)
    key = 'contents'
    session.set_response({key: [sample_spec]})

    # When
    specs = collection.get_specs(test_scope, test_id)

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method="GET",
        path="projects/{}/material-templates/{}/{}/material-specs".format(project_id, test_scope, test_id),
    )
    assert session.last_call == expected_call
    assert key in specs
    output = specs[key]
    assert 1 == len(output)
    assert output == [sample_spec]


def test_get_runs(collection, session, spec_collection):
    # Given
    project_id = '6b608f78-e341-422c-8076-35adc8828545'
    material_template = MaterialTemplateFactory()
    test_scope = 'id'
    template_id = material_template.uids[test_scope]
    sample_spec1 = MaterialSpecDataFactory(template=template_id)
    sample_spec2 = MaterialSpecDataFactory(template=template_id)
    key = 'contents'
    sample_run1 = MaterialRunDataFactory(spec=sample_spec1['uids'][test_scope])
    sample_run2 = MaterialRunDataFactory(spec=sample_spec2['uids'][test_scope])
    session.set_responses({key: [sample_spec1, sample_spec2]}, {key: [sample_run1]}, {key: [sample_run2]})

    # When
    runs = collection.get_runs(test_scope, template_id, spec_collection)

    # Then
    assert 3 == session.num_calls
    output = runs[key]
    assert 2 == len(output)
    assert output == [sample_run1, sample_run2]