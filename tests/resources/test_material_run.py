from uuid import UUID

import pytest
from citrine._session import Session
from citrine._utils.functions import scrub_none
from citrine.exceptions import BadRequest
from citrine.resources.api_error import ValidationError
from citrine.resources.material_run import MaterialRunCollection
from gemd.entity.bounds.integer_bounds import IntegerBounds
from gemd.entity.object.material_run import MaterialRun as GEMDRun

from tests.resources.test_data_concepts import run_noop_gemd_relation_search_test
from tests.utils.factories import MaterialRunFactory, MaterialRunDataFactory, LinkByUIDFactory, MaterialSpecFactory, \
    MaterialTemplateFactory, MaterialSpecDataFactory, ProcessTemplateFactory
from tests.utils.session import FakeSession, FakeCall, make_fake_cursor_request_function, FakeRequestResponseApiError, \
    FakeRequestResponse


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


def test_register_all(collection, session):
    runs = [MaterialRunFactory(name='1'), MaterialRunFactory(name='2'),  MaterialRunFactory(name='3')]
    session.set_response({'objects': [r.dump() for r in runs]})
    registered = collection.register_all(runs)
    assert [r.name for r in runs] == [r.name for r in registered]
    assert len(session.calls) == 1
    assert session.calls[0].method == 'PUT'
    assert session.calls[0].path == 'projects/{}/datasets/{}/material-runs/batch'.format(
        collection.project_id, collection.dataset_id)
    with pytest.raises(RuntimeError):
        MaterialRunCollection(collection.project_id, dataset_id=None, session=session).register_all([])


def test_dry_run_register_material_run(collection, session):
    # Given
    session.set_response(MaterialRunDataFactory(name='Test MR 123'))
    material_run = MaterialRunFactory()

    # When
    registered = collection.register(material_run, dry_run=True)

    # Then
    assert "<Material run 'Test MR 123'>" == str(registered)
    assert session.last_call.params == {'dry_run': True}


def test_nomutate_gemd(collection, session):
    """When registering a GEMD object, the object should not change (aside from auto ids)"""
    # Given
    session.set_response(MaterialRunDataFactory(name='Test MR mutation'))
    before, after = (GEMDRun(name='Main', uids={'nomutate': 'please'}) for i in range(2))

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
    run = collection.get_history(scope='id', id='1234')

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
    runs = list(collection.list())

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='GET',
        path='projects/{}/material-runs'.format(collection.project_id),
        params={
            'dataset_id': str(collection.dataset_id),
            'forward': True,
            'ascending': True,
            'per_page': 100
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
    assert len(list(collection.list(per_page=2))) == len(all_runs)
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
        params={'dry_run': False}
    )
    assert expected_call == session.last_call

def test_dry_run_delete_material_run(collection, session):
    # Given
    material_run_uid = '2d3a782f-aee7-41db-853c-36bf4bff0626'
    material_run_scope = 'id'

    # When
    collection.delete(material_run_uid, dry_run=True)

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
        params={'dry_run': True}
    )
    assert expected_call == session.last_call


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


def test_get_by_process(collection):
    run_noop_gemd_relation_search_test(
        search_for='material-runs',
        search_with='process-runs',
        collection=collection,
        search_fn=collection.get_by_process,
        per_page=1,
    )


def test_list_by_spec(collection):
    run_noop_gemd_relation_search_test(
        search_for='material-runs',
        search_with='material-specs',
        collection=collection,
        search_fn=collection.list_by_spec,
    )


def test_validate_templates_successful_minimal_params(collection, session):
    """
    Test that DataObjectCollection.validate_templates() handles a successful return value when
    passing in minimal params
    """

    # Given
    project_id = '6b608f78-e341-422c-8076-35adc8828545'
    run = MaterialRunFactory(name="validate_templates_successful")

    # When
    session.set_response("")
    errors = collection.validate_templates(model=run)

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method="PUT",
        path="projects/{}/material-runs/validate-templates".format(project_id),
        json={"dataObject":scrub_none(run.dump())})
    assert session.last_call == expected_call
    assert errors == []


def test_validate_templates_successful_all_params(collection, session):
    """
    Test that DataObjectCollection.validate_templates() handles a successful return value when
    passing in all params
    """

    # Given
    project_id = '6b608f78-e341-422c-8076-35adc8828545'
    run = MaterialRunFactory(name="validate_templates_successful")
    template = MaterialTemplateFactory()
    unused_process_template = ProcessTemplateFactory()

    # When
    session.set_response("")
    errors = collection.validate_templates(model=run, object_template=template, ingredient_process_template=unused_process_template)

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method="PUT",
        path="projects/{}/material-runs/validate-templates".format(project_id),
        json={"dataObject": scrub_none(run.dump()),
              "objectTemplate": scrub_none(template.dump()),
              "ingredientProcessTemplate": scrub_none(unused_process_template.dump())})
    assert session.last_call == expected_call
    assert errors == []


def test_validate_templates_errors(collection, session):
    """
    Test that DataObjectCollection.validate_templates() handles validation errors
    """
    # Given
    project_id = '6b608f78-e341-422c-8076-35adc8828545'
    run = MaterialRunFactory(name="")

    # When
    validation_error = ValidationError(failure_message="you failed", failure_id="failure_id")
    session.set_response(BadRequest("path", FakeRequestResponseApiError(400, "Bad Request", [validation_error])))
    errors = collection.validate_templates(model=run)

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method="PUT",
        path="projects/{}/material-runs/validate-templates".format(project_id),
        json={"dataObject":scrub_none(run.dump())})
    assert session.last_call == expected_call
    assert errors == [validation_error]


def test_validate_templates_unrelated_400(collection, session):
    """
    Test that DataObjectCollection.validate_templates() propagates an unrelated 400
    """
    # Given
    run = MaterialRunFactory()

    # When
    session.set_response(BadRequest("path", FakeRequestResponse(400)))
    with pytest.raises(BadRequest):
        collection.validate_templates(model=run)


def test_validate_templates_unrelated_400_with_api_error(collection, session):
    """
    Test that DataObjectCollection.validate_templates() propagates an unrelated 400
    """
    # Given
    run = MaterialRunFactory()

    # When
    session.set_response(BadRequest("path", FakeRequestResponseApiError(400, "I am not a validation error", [])))
    with pytest.raises(BadRequest):
        collection.validate_templates(model=run)


def test_list_by_template(collection, session):
    """
    Test that MaterialRunCollection.list_by_template() hits the expected endpoints and post-processes the results into the expected format
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
    runs = [run for run in collection.list_by_template(template_id)]

    # Then
    assert 3 == session.num_calls
    assert runs == [collection.build(run) for run in [sample_run1_1, sample_run1_2, sample_run2_1, sample_run2_2]]
