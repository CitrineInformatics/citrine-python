from uuid import UUID

import pytest
from citrine.resources.material_spec import MaterialSpecCollection
from citrine.resources.material_template import MaterialTemplateCollection

from tests.utils.factories import MaterialTemplateFactory, MaterialSpecDataFactory, MaterialRunDataFactory
from tests.utils.session import FakeCall, FakeSession


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
    """
    Test that MaterialTemplateCollection.get_specs() hits the expected endpoint
    """
    # Given
    project_id = '6b608f78-e341-422c-8076-35adc8828545'
    material_template = MaterialTemplateFactory()
    test_scope = 'id'
    test_id = material_template.uids[test_scope]
    sample_spec = MaterialSpecDataFactory(template=test_id)
    session.set_response({'contents': [sample_spec]})

    # When
    specs = [spec for spec in collection.get_specs(test_scope, test_id)]

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method="GET",
        path="projects/{}/material-templates/{}/{}/material-specs".format(project_id, test_scope, test_id),
        params={"forward": True, "ascending": True, "per_page": 20}
    )
    assert session.last_call == expected_call
    assert 1 == len(specs)
    assert specs == [sample_spec]


def test_get_runs(collection, session, spec_collection):
    """
    Test that MaterialTemplateCollection.get_runs() hits the expected endpoints and post-processes the results into the expected format
    """
    # Given
    material_template = MaterialTemplateFactory()
    test_scope = 'id'
    template_id = material_template.uids[test_scope]
    sample_spec1 = MaterialSpecDataFactory(template=template_id)
    sample_spec2 = MaterialSpecDataFactory(template=template_id)
    key = 'contents'
    sample_run1_1 = MaterialRunDataFactory(spec=sample_spec1['uids'][test_scope])
    sample_run2_1 = MaterialRunDataFactory(spec=sample_spec2['uids'][test_scope])
    sample_run1_2 = MaterialRunDataFactory(spec=sample_spec1['uids'][test_scope])
    sample_run2_2 = MaterialRunDataFactory(spec=sample_spec2['uids'][test_scope])
    session.set_responses({key: [sample_spec1, sample_spec2]}, {key: [sample_run1_1, sample_run1_2]}, {key: [sample_run2_1, sample_run2_2]})

    # When
    runs = [run for run in collection.get_runs(test_scope, template_id, spec_collection, per_page=1)]

    # Then
    assert 3 == session.num_calls
    assert 4 == len(runs)
    assert runs == [sample_run1_1, sample_run1_2, sample_run2_1, sample_run2_2]
