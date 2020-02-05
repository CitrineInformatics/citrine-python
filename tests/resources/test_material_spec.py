from uuid import UUID

import pytest
from citrine.resources.material_spec import MaterialSpecCollection

from tests.utils.factories import MaterialSpecFactory, MaterialRunDataFactory
from tests.utils.session import FakeSession, FakeCall


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def collection(session) -> MaterialSpecCollection:
    return MaterialSpecCollection(
        project_id=UUID('6b608f78-e341-422c-8076-35adc8828545'),
        dataset_id=UUID('8da51e93-8b55-4dd3-8489-af8f65d4ad9a'),
        session=session)


def test_get_runs(collection, session):
    # Given
    project_id = '6b608f78-e341-422c-8076-35adc8828545'
    material_spec = MaterialSpecFactory()
    test_scope = 'id'
    test_id = material_spec.uids[test_scope]
    sample_run = MaterialRunDataFactory(spec=test_id)
    key = 'contents'
    session.set_response({key: [sample_run]})

    # When
    runs = collection.get_runs(test_scope, test_id)

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method="GET",
        path="projects/{}/material-specs/{}/{}/material-runs".format(project_id, test_scope, test_id),
    )
    assert session.last_call == expected_call
    assert key in runs
    output = runs[key]
    assert 1 == len(output)
    assert output == [sample_run]
