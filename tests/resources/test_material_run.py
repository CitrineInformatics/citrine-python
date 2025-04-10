from uuid import UUID
import json

import pytest
from citrine._session import Session
from citrine._utils.functions import scrub_none
from citrine.exceptions import BadRequest
from citrine.resources.api_error import ValidationError
from citrine.resources.data_concepts import CITRINE_SCOPE
from citrine.resources.material_run import MaterialRunCollection
from citrine.resources.material_run import MaterialRun as CitrineRun
from citrine.resources.material_run import _inject_default_label_tags
from citrine.resources.gemd_resource import GEMDResourceCollection

from gemd.demo.cake import make_cake, change_scope
from gemd.entity.bounds.integer_bounds import IntegerBounds
from gemd.entity.link_by_uid import LinkByUID
from gemd.entity.object.material_run import MaterialRun as GEMDRun
from gemd.entity.object.material_spec import MaterialSpec as GEMDSpec
from gemd.json import GEMDJson
from gemd.util import flatten

from tests.resources.test_data_concepts import run_noop_gemd_relation_search_test
from tests.utils.factories import MaterialRunFactory, MaterialRunDataFactory, LinkByUIDFactory, \
    MaterialTemplateFactory, MaterialSpecDataFactory, ProcessTemplateFactory
from tests.utils.session import FakeSession, FakeCall, make_fake_cursor_request_function, FakeRequestResponseApiError, \
    FakeRequestResponse


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def collection(session) -> MaterialRunCollection:
    return MaterialRunCollection(
        dataset_id=UUID('8da51e93-8b55-4dd3-8489-af8f65d4ad9a'),
        session=session,
        team_id = UUID('6b608f78-e341-422c-8076-35adc8828000'))

def test_deprecated_collection_construction(session):
    with pytest.deprecated_call():
        team_id = UUID('6b608f78-e341-422c-8076-35adc8828000')
        check_project = {'project': {'team': {'id': team_id}}}
        session.set_response(check_project)
        mr =  MaterialRunCollection(
            dataset_id=UUID('8da51e93-8b55-4dd3-8489-af8f65d4ad9a'),
            session=session,
            project_id=UUID('6b608f78-e341-422c-8076-35adc8828545'))

def test_invalid_collection_construction():
    with pytest.raises(TypeError):
        mr = MaterialRunCollection(dataset_id=UUID('8da51e93-8b55-4dd3-8489-af8f65d4ad9a'),
                                   session=session)


def test_register_material_run(collection, session):
    # Given
    session.set_response(MaterialRunDataFactory(name='Test MR 123'))
    material_run = MaterialRunFactory()

    # When
    registered = collection.register(material_run)

    # Then
    assert "<Material run 'Test MR 123'>" == str(registered)


def test_register_all(collection, session):
    runs = [MaterialRunFactory(name='1'), MaterialRunFactory(name='2'), MaterialRunFactory(name='3')]
    session.set_response({'objects': [r.dump() for r in runs]})
    registered = collection.register_all(runs)
    assert [r.name for r in runs] == [r.name for r in registered]
    assert len(session.calls) == 1
    assert session.calls[0].method == 'PUT'
    assert GEMDResourceCollection(team_id = collection.team_id, dataset_id = collection.dataset_id, session = collection.session)._get_path() \
           in session.calls[0].path
    with pytest.raises(RuntimeError):
        MaterialRunCollection(team_id=collection.team_id, dataset_id=None, session=session).register_all([])


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
    before, after = (GEMDRun(name='Main', uids={'nomutate': 'please'}) for _ in range(2))

    # When
    registered = collection.register(after)

    # Then
    assert after.uids.pop(CITRINE_SCOPE) is not None
    assert before == after
    assert "<Material run 'Test MR mutation'>" == str(registered)
    assert registered.uid is not None


def test_get_history(collection, session):
    # Given
    cake = make_cake()
    cake_json = json.loads(GEMDJson(scope=CITRINE_SCOPE).dumps(cake))
    root_link = LinkByUID.build(cake_json.pop('object'))
    root_obj = next(o for o in cake_json['context'] if root_link.id == o['uids'].get(root_link.scope))
    cake_json['roots'] = [root_obj]
    cake_json['context'].remove(root_obj)

    session.set_response([cake_json])

    # When
    run = collection.get_history(id=root_link)

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='POST',
        path=f'teams/{collection.team_id}/gemd/query/material-histories?filter_nonroot_materials=true',
        json={
            'criteria': [
                {
                    'datasets': [str(collection.dataset_id)],
                    'type': 'terminal_material_run_identifiers_criteria',
                    'terminal_material_ids': [{'scope': root_link.scope, 'id': root_link.id}]
                }
            ]
        }
    )
    assert expected_call == session.last_call
    assert run == cake


def test_get_history_no_histories(collection, session):
    # Given
    root_id = UUID("b1037885-d46e-49aa-867f-2a2372b6dc63")

    session.set_response([])

    # When
    run = collection.get_history(id=root_id)

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='POST',
        path=f'teams/{collection.team_id}/gemd/query/material-histories?filter_nonroot_materials=true',
        json={
            'criteria': [
                {
                    'datasets': [str(collection.dataset_id)],
                    'type': 'terminal_material_run_identifiers_criteria',
                    'terminal_material_ids': [{'scope': CITRINE_SCOPE, 'id': str(root_id)}]
                }
            ]
        }
    )
    assert expected_call == session.last_call
    assert run is None


def test_get_history_no_roots(collection, session):
    # Given
    cake = make_cake()
    cake_json = json.loads(GEMDJson(scope=CITRINE_SCOPE).dumps(cake))
    root_link = LinkByUID.build(cake_json.pop('object'))
    root_obj = next(o for o in cake_json['context'] if root_link.id == o['uids'].get(root_link.scope))
    cake_json['roots'] = []
    cake_json['context'].remove(root_obj)

    session.set_response([cake_json])

    # When
    run = collection.get_history(id=root_link)

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='POST',
        path=f'teams/{collection.team_id}/gemd/query/material-histories?filter_nonroot_materials=true',
        json={
            'criteria': [
                {
                    'datasets': [str(collection.dataset_id)],
                    'type': 'terminal_material_run_identifiers_criteria',
                    'terminal_material_ids': [{'scope': root_link.scope, 'id': root_link.id}]
                }
            ]
        }
    )
    assert expected_call == session.last_call
    assert run is None


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
        path='teams/{}/datasets/{}/material-runs/id/{}'.format(collection.team_id, collection.dataset_id, mr_id)
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
        path='teams/{}/material-runs'.format(collection.team_id, collection.dataset_id),
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
        path='teams/{}/datasets/{}/material-runs/{}/{}'.format(
            collection.team_id,
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
        path='teams/{}/datasets/{}/material-runs/{}/{}'.format(
            collection.team_id,
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
        path='teams/{}/material-runs/id/{}'.format(collection.team_id, mr_id)
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
    team_id = collection.team_id
    run = MaterialRunFactory(name="validate_templates_successful")

    # When
    session.set_response("")
    errors = collection.validate_templates(model=run)

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method="PUT",
        path="teams/{}/material-runs/validate-templates".format(team_id),
        json={"dataObject": scrub_none(run.dump())})
    assert session.last_call == expected_call
    assert errors == []


def test_validate_templates_successful_all_params(collection, session):
    """
    Test that DataObjectCollection.validate_templates() handles a successful return value when
    passing in all params
    """

    # Given
    team_id = collection.team_id
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
        path="teams/{}/material-runs/validate-templates".format(team_id),
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
    team_id = collection.team_id
    run = MaterialRunFactory(name="")

    # When
    validation_error = ValidationError.build({"failure_message": "you failed", "failure_id": "failure_id"})
    session.set_response(BadRequest("path", FakeRequestResponseApiError(400, "Bad Request", [validation_error])))
    errors = collection.validate_templates(model=run)

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method="PUT",
        path="teams/{}/material-runs/validate-templates".format(team_id),
        json={"dataObject": scrub_none(run.dump())})
    assert session.last_call == expected_call
    assert len(errors) == 1
    assert errors[0].dump() == validation_error.dump()


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


def test_equals():
    """Test basic equality.  Complex relationships are tested in test_material_run.test_deep_equals()."""
    from citrine.resources.material_run import MaterialRun as CitrineMaterialRun
    from gemd.entity.object import MaterialRun as GEMDMaterialRun

    gemd_obj = GEMDMaterialRun(
        name="My Name",
        notes="I have notes",
        tags=["tag!"]
    )
    citrine_obj = CitrineMaterialRun(
        name="My Name",
        notes="I have notes",
        tags=["tag!"]
    )
    assert gemd_obj == citrine_obj, "GEMD/Citrine equivalence"
    citrine_obj.notes = "Something else"
    assert gemd_obj != citrine_obj, "GEMD/Citrine detects difference"


def test_deep_equals(collection):
    change_scope('test_deep_equals_scope')
    cake = make_cake()
    flat_list = flatten(cake)
    # Note that registered turns them into a flat list of Citrine resources
    registered = set(collection.register_all(flat_list))
    assert len(flat_list) == len(registered), "All objects registered"
    while flat_list:
        before = flat_list.pop()
        afters = [x for x in registered if x == before]
        assert len(afters) >= 1, "All flattened objects were registered"
        for x in afters:
            registered.remove(x)
    assert len(registered) == 0, "All registered objects are in the flat list"

    assert cake == CitrineRun.build(cake.dump()), "Equality works in hydrated form"


def test_nonmutating_dry_run(collection):
    change_scope('test_deep_equals_scope')
    cake = make_cake()
    uid_stash = cake.uids.copy()

    flat_list = flatten(cake)
    # Note that registered turns them into a flat list of Citrine resources
    tested = set(collection.register_all(flat_list, dry_run=True))
    assert uid_stash == cake.uids  # No mutation

    # Note that the lists are different lengths because of how dry_run batching works
    while flat_list:
        before = flat_list.pop()
        afters = [x for x in tested if x == before]
        assert len(afters) >= 1, "All flattened objects were registered"
        for x in afters:
            tested.remove(x)
    assert len(tested) == 0, "All registered objects are in the flat list"


def test_args_only(collection):
    """"Test that only arguments to register_all get registered/tested/returned."""
    obj = GEMDRun("name", spec=GEMDSpec("name"))
    GEMDJson(scope='test_args_only').dumps(obj)  # no-op to populate ids
    dry = collection.register_all([obj], dry_run=True)
    assert obj in dry
    assert obj.spec not in dry

    not_dry = collection.register_all([obj], dry_run=False)
    assert obj in not_dry
    assert obj.spec not in not_dry
