import random
from uuid import UUID

import pytest

from citrine.resources.gemd_resource import GEMDResourceCollection
from citrine.resources.material_run import MaterialRun
from citrine.resources.material_spec import MaterialSpec

from tests.utils.factories import MaterialRunFactory, MaterialSpecFactory, MaterialTemplateFactory
from tests.utils.session import FakeSession, FakeCall


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def collection(session) -> GEMDResourceCollection:
    return GEMDResourceCollection(
        project_id=UUID('6b608f78-e341-422c-8076-35adc8828545'),
        dataset_id=UUID('8da51e93-8b55-4dd3-8489-af8f65d4ad9a'),
        session=session
    )


def sample_gems(nsamples, **kwargs):
    factories = [MaterialRunFactory, MaterialSpecFactory, MaterialTemplateFactory]
    return [
        random.choice(factories)(**kwargs) for _ in range(nsamples)
    ]


def test_get(collection, session):
    # Given
    run = MaterialRunFactory(name='foo')
    mr_id = run.uids['id']
    session.set_response(run)

    # When
    gem = collection.get(mr_id)

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='GET',
        path='projects/{}/storables/id/{}'.format(collection.project_id, mr_id)
    )
    print(session.last_call)
    assert expected_call == session.last_call
    assert 'foo' == gem.name


def test_list(collection, session):
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
        path='projects/{}/storables'.format(collection.project_id),
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
        assert samples[i].uids == gems[i].uids


def test_list_by_name(collection, session):
    # Given
    samples = sample_gems(20, name='foobar')
    session.set_response({
        'contents': samples
    })

    # When
    gems = list(collection.list_by_name('foobar', exact=True))

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='GET',
        path='projects/{}/storables/filter-by-name'.format(collection.project_id),
        params={
            'dataset_id': str(collection.dataset_id),
            'name': 'foobar',
            'exact': True,
            'forward': True,
            'ascending': True,
            'per_page': 100
        }
    )
    assert expected_call == session.last_call
    assert len(samples) == len(gems)

    # Invalid input
    with pytest.raises(RuntimeError):
        collection.dataset_id = None
        collection.list_by_name('foo', per_page=2)


def test_list_by_tag(collection, session):
    # Given
    samples = sample_gems(20, tags=['foo::bar'])
    session.set_response({
        'contents': samples
    })

    # When
    gems = list(collection.list_by_tag('foo::bar'))

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='GET',
        path='projects/{}/storables'.format(collection.project_id),
        params={
            'dataset_id': str(collection.dataset_id),
            'tags': ['foo::bar'],
            'forward': True,
            'ascending': True,
            'per_page': 100
        }
    )
    assert expected_call == session.last_call
    assert len(samples) == len(gems)


def test_update(collection):
    with pytest.raises(NotImplementedError):
        collection.update(MaterialRun('foo'))


def test_delete(collection):
    with pytest.raises(NotImplementedError):
        collection.delete(MaterialRun('foo'))


def test_register(collection):
    with pytest.raises(NotImplementedError):
        collection.register(MaterialRun('foo'))


def test_register_all(collection):
    with pytest.raises(NotImplementedError):
        collection.register_all([MaterialRun('foo'), MaterialSpec('foo')])