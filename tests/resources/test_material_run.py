from uuid import UUID

import pytest
from citrine._session import Session
from citrine.resources.material_run import MaterialRunCollection, MaterialRun
from taurus.entity.object.material_run import MaterialRun as TaurusRun
from taurus.entity.bounds.integer_bounds import IntegerBounds

from tests.utils.factories import MaterialRunFactory, MaterialRunDataFactory, LinkByUIDFactory, MaterialSpecFactory, \
    MaterialTemplateFactory, MaterialSpecDataFactory
from tests.utils.session import FakeSession, FakeCall, make_fake_cursor_request_function


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def collection(session) -> MaterialRunCollection:
    return MaterialRunCollection(
        project_id=UUID('6b608f78-e341-422c-8076-35adc8828545'),
        dataset_id=UUID('8da51e93-8b55-4dd3-8489-af8f65d4ad9a'),
        session=session
    )


def test_register_material_run(collection, session):
    # Given
    session.set_response(MaterialRunDataFactory(name='Test MR 123'))
    material_run = MaterialRunFactory()

    # When
    registered = collection.register(material_run)

    # Then
    assert "<Material run 'Test MR 123'>" == str(registered)


def test_nomutate_taurus(collection, session):
    """When registering a Taurus object, the object should not change (aside from auto ids)"""
    # Given
    session.set_response(MaterialRunDataFactory(name='Test MR mutation'))
    before, after = (TaurusRun(name='Main', uids={'nomutate': 'please'}) for i in range(2))

    # When
    registered = collection.register(after)

    # Then
    assert before == after
    assert "<Material run 'Test MR mutation'>" == str(registered)


def test_get_history(collection, session):
    # Given
    session.set_response({
        'context': [],
        'root': MaterialRunDataFactory(name='Historic MR')
    })

    # When
    run = collection.get_history('id', '1234')

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='GET',
        path='projects/{}/material-history/id/1234'.format(collection.project_id)
    )
    assert expected_call == session.last_call
    assert 'Historic MR' == run.name


def test_get_material_run(collection, session):
    # Given
    run_data = MaterialRunDataFactory(name='Cake 2')
    mr_id = run_data['uids']['id']
    session.set_response(run_data)

    # When
    run = collection.get(mr_id)

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='GET',
        path='projects/{}/datasets/{}/material-runs/id/{}'.format(collection.project_id, collection.dataset_id, mr_id)
    )
    assert expected_call == session.last_call
    assert 'Cake 2' == run.name


def test_list_material_runs(collection, session):
    # Given
    sample_run = MaterialRunDataFactory()
    session.set_response({
        'contents': [sample_run]
    })

    # When
    runs = collection.list()

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='GET',
        path='projects/{}/material-runs'.format(collection.project_id),
        params={
            'dataset_id': str(collection.dataset_id),
            'tags': [],
            'per_page': 100
        }
    )
    assert expected_call == session.last_call
    assert 1 == len(runs)
    assert sample_run['uids'] == runs[0].uids


def test_filter_by_tags(collection, session):
    # Given
    sample_run = MaterialRunDataFactory()
    session.set_response({
        'contents': [sample_run]
    })

    # When
    runs = collection.filter_by_tags(tags=["color"], page=1, per_page=10)

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='GET',
        path='projects/{}/material-runs'.format(collection.project_id),
        params={
            'dataset_id': str(collection.dataset_id),
            'tags': ["color"],
            'page': 1,
            'per_page': 10
        }
    )
    assert expected_call == session.last_call
    assert 1 == len(runs)
    assert sample_run['uids'] == runs[0].uids

    # When user gives a single string for tags, it should still work.
    collection.filter_by_tags(tags="color", page=1, per_page=10)

    # Then
    assert session.num_calls == 2
    assert session.last_call == expected_call

    # When user gives multiple tags, should raise NotImplemented Error
    with pytest.raises(NotImplementedError):
        collection.filter_by_tags(tags=["color", "shape"])


def test_filter_by_name(collection, session):
    # Given
    sample_run = MaterialRunDataFactory()
    session.set_response({'contents': [sample_run]})

    # When
    runs = collection.filter_by_name('test run', page=1, per_page=10)

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='GET',
        path='projects/{}/material-runs/filter-by-name'.format(collection.project_id),
        params={
            'dataset_id': str(collection.dataset_id),
            'name': 'test run',
            'exact': False,
            "page": 1,
            "per_page": 10
        }
    )
    assert expected_call == session.last_call
    assert 1 == len(runs)
    assert sample_run['uids'] == runs[0].uids


def test_cursor_paginated_searches(collection, session):
    """
    Tests that search methods using cursor-pagination are hooked up correctly.
    There is no real search logic tested here.
    """
    all_runs = [
        MaterialRunDataFactory(name="foo_{}".format(i)) for i in range(20)
    ]
    fake_request = make_fake_cursor_request_function(all_runs)
    # pretty shady, need to add these methods to the fake session to test their
    # interactions with the actual search methods
    setattr(session, 'get_resource', fake_request)
    setattr(session, 'post_resource', fake_request)
    setattr(session, 'cursor_paged_resource', Session.cursor_paged_resource)

    assert len(list(collection.list_by_name('unused', per_page=2))) == len(all_runs)
    assert len(list(collection.list_all(per_page=2))) == len(all_runs)
    assert len(list(collection.list_by_tag('unused', per_page=2))) == len(all_runs)
    assert len(list(collection.list_by_attribute_bounds(
        {LinkByUIDFactory(): IntegerBounds(1, 5)}, per_page=2))) == len(all_runs)

    # invalid inputs
    with pytest.raises(TypeError):
        collection.list_by_attribute_bounds([1, 5], per_page=2)
    with pytest.raises(NotImplementedError):
        collection.list_by_attribute_bounds({
            LinkByUIDFactory(): IntegerBounds(1, 5),
            LinkByUIDFactory(): IntegerBounds(1, 5),
        }, per_page=2)
    with pytest.raises(RuntimeError):
        collection.dataset_id = None
        collection.list_by_name('unused', per_page=2)


def test_filter_by_attribute_bounds(collection, session):
    # Given
    sample_run = MaterialRunDataFactory()
    session.set_response({'contents': [sample_run]})
    link = LinkByUIDFactory()
    bounds = {link: IntegerBounds(1, 5)}

    # When
    runs = collection.filter_by_attribute_bounds(bounds, page=1, per_page=10)

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='POST',
        path='projects/{}/material-runs/filter-by-attribute-bounds'.format(collection.project_id),
        params={
            "page": 1,
            "per_page": 10,
            "dataset_id": str(collection.dataset_id)
        },
        json={
            'attribute_bounds': {
                link.id: {'lower_bound': 1, 'upper_bound': 5, 'type': 'integer_bounds'}
            }
        }
    )
    assert expected_call == session.last_call
    assert 1 == len(runs)
    assert sample_run['uids'] == runs[0].uids


def test_delete_material_run(collection, session):
    # Given
    material_run_uid = '2d3a782f-aee7-41db-853c-36bf4bff0626'
    material_run_scope = 'id'

    # When
    collection.delete(material_run_uid)

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='DELETE',
        path='projects/{}/datasets/{}/material-runs/{}/{}'.format(
            collection.project_id,
            collection.dataset_id,
            material_run_scope,
            material_run_uid
        ),
    )
    assert expected_call == session.last_call


def test_build_discarded_objects_in_material_run():
    # Note:  This is really here just for test coverage - couldn't figure out how to
    #        get past the validation/serialization in MaterialRun.build - it might just be dead code
    material_run = MaterialRunFactory()
    material_run_data = MaterialRunDataFactory(
        name='Test Run',
        measurements=LinkByUIDFactory.create_batch(3)
    )

    MaterialRun._build_discarded_objects(material_run, material_run_data, None)


def test_material_run_cannot_register_with_no_id(collection):
    # Given
    collection.dataset_id = None

    # Then
    with pytest.raises(RuntimeError):
        collection.register(MaterialRunFactory())


def test_material_run_can_get_with_no_id(collection, session):
    # Given
    collection.dataset_id = None

    run_data = MaterialRunDataFactory(name='Cake 2')
    mr_id = run_data['uids']['id']
    session.set_response(run_data)

    # When
    run = collection.get(mr_id)

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='GET',
        path='projects/{}/material-runs/id/{}'.format(collection.project_id, mr_id)
    )
    assert expected_call == session.last_call
    assert 'Cake 2' == run.name


def test_material_run_filter_by_name_with_no_id(collection):
    # Given
    collection.dataset_id = None

    # Then
    with pytest.raises(RuntimeError):
        collection.filter_by_name('foo')


def test_filter_by_spec(collection, session):
    """
    Test that MaterialRunCollection.filter_by_spec() hits the expected endpoint
    """
    # Given
    project_id = '6b608f78-e341-422c-8076-35adc8828545'
    material_spec = MaterialSpecFactory()
    test_scope = 'id'
    test_id = material_spec.uids[test_scope]
    sample_run = MaterialRunDataFactory(spec=material_spec)
    session.set_response({'contents': [sample_run]})

    # When
    runs = [run for run in collection.filter_by_spec(test_id)]

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method="GET",
        path="projects/{}/material-specs/{}/{}/material-runs".format(project_id, test_scope, test_id),
        params={"forward": True, "ascending": True, "per_page": 20}
    )
    assert session.last_call == expected_call
    assert runs == [collection.build(sample_run)]


def test_filter_by_template(collection, session):
    """
    Test that MaterialRunCollection.filter_by_template() hits the expected endpoints and post-processes the results into the expected format
    """
    # Given
    material_template = MaterialTemplateFactory()
    test_scope = 'id'
    template_id = material_template.uids[test_scope]
    sample_spec1 = MaterialSpecDataFactory(template=material_template)
    sample_spec2 = MaterialSpecDataFactory(template=material_template)
    key = 'contents'
    sample_run1_1 = MaterialRunDataFactory(spec=sample_spec1)
    sample_run2_1 = MaterialRunDataFactory(spec=sample_spec2)
    sample_run1_2 = MaterialRunDataFactory(spec=sample_spec1)
    sample_run2_2 = MaterialRunDataFactory(spec=sample_spec2)
    session.set_responses({key: [sample_spec1, sample_spec2]}, {key: [sample_run1_1, sample_run1_2]},
                          {key: [sample_run2_1, sample_run2_2]})

    # When
    runs = [run for run in collection.filter_by_template(template_id, per_page=1)]

    # Then
    assert 3 == session.num_calls
    assert runs == [collection.build(run) for run in [sample_run1_1, sample_run1_2, sample_run2_1, sample_run2_2]]