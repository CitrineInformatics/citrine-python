import uuid
import random

import pytest

from citrine.resources.data_concepts import DataConcepts
from citrine.resources.gemd_resource import GEMDResourceCollection
from citrine._utils.functions import format_escaped_url

from tests.utils.factories import MaterialRunDataFactory, MaterialSpecDataFactory
from tests.utils.session import FakeSession, FakeCall


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def collection(session) -> GEMDResourceCollection:
    return GEMDResourceCollection(
        project_id=uuid.uuid4(),
        dataset_id=uuid.uuid4(),
        session=session
    )


def sample_gems(nsamples, **kwargs):
    factories = [MaterialRunDataFactory, MaterialSpecDataFactory]
    return [random.choice(factories)(**kwargs) for _ in range(nsamples)]


def test_gemd(collection, session):
    # Given
    samples = sample_gems(20)
    session.set_response({
        'contents': samples
    })

    # When
    gems = list(collection.list())

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='GET',
        path=format_escaped_url('projects/{}/storables', collection.project_id),
        params={
            'dataset_id': str(collection.dataset_id),
            'forward': True,
            'ascending': True,
            'per_page': 100
        }
    )
    assert expected_call == session.last_call
    assert len(samples) == len(gems)
    for i in range(len(gems)):
        assert samples[i]['uids']['id'] == gems[i].uids['id']

    # Test return type
    assert DataConcepts == collection.get_type()
