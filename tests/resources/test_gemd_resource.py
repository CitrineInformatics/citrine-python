import random
from uuid import uuid4, UUID
from os.path import basename

import pytest

from gemd.entity.bounds.integer_bounds import IntegerBounds
from gemd.entity.attribute import Condition
from gemd.entity.value import NominalInteger
from gemd.entity.link_by_uid import LinkByUID
from gemd.entity.object.material_spec import MaterialSpec as GemdMaterialSpec
from gemd.entity.object.process_spec import ProcessSpec as GemdProcessSpec

from citrine.exceptions import PollingTimeoutError, JobFailureError
from citrine.resources.api_error import ApiError, ValidationError
from citrine.resources.audit_info import AuditInfo
from citrine.resources.condition_template import ConditionTemplateCollection, ConditionTemplate
from citrine.resources.data_concepts import DataConcepts, CITRINE_SCOPE, CITRINE_TAG_PREFIX
from citrine.resources.gemd_resource import GEMDResourceCollection
from citrine.resources.ingredient_run import IngredientRun, IngredientRunCollection
from citrine.resources.ingredient_spec import IngredientSpec, IngredientSpecCollection
from citrine.resources.material_run import MaterialRunCollection, MaterialRun
from citrine.resources.material_spec import MaterialSpecCollection, MaterialSpec
from citrine.resources.material_template import MaterialTemplateCollection, MaterialTemplate
from citrine.resources.measurement_run import MeasurementRunCollection, MeasurementRun
from citrine.resources.measurement_spec import MeasurementSpec, MeasurementSpecCollection
from citrine.resources.measurement_template import MeasurementTemplate, \
    MeasurementTemplateCollection
from citrine.resources.parameter_template import ParameterTemplateCollection, ParameterTemplate
from citrine.resources.process_run import ProcessRunCollection, ProcessRun
from citrine.resources.process_spec import ProcessSpecCollection, ProcessSpec
from citrine.resources.process_template import ProcessTemplateCollection, ProcessTemplate
from citrine.resources.property_template import PropertyTemplateCollection, PropertyTemplate
from citrine._utils.functions import format_escaped_url

from tests.utils.factories import MaterialRunDataFactory, MaterialSpecDataFactory
from tests.utils.factories import JobSubmissionResponseFactory
from tests.utils.session import FakeSession, FakeCall


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def gemd_collection(session) -> GEMDResourceCollection:
    return GEMDResourceCollection(
        project_id=uuid4(),
        dataset_id=uuid4(),
        session=session
    )


def sample_gems(nsamples, **kwargs):
    factories = [MaterialRunDataFactory, MaterialSpecDataFactory]
    return [random.choice(factories)(**kwargs) for _ in range(nsamples)]


def test_get_type(gemd_collection):
    assert DataConcepts == gemd_collection.get_type()


def test_list(gemd_collection, session):
    # Given
    samples = sample_gems(20)
    session.set_response({
        'contents': samples
    })

    # When
    gems = list(gemd_collection.list())

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='GET',
        path=format_escaped_url('projects/{}/storables', gemd_collection.project_id),
        params={
            'dataset_id': str(gemd_collection.dataset_id),
            'forward': True,
            'ascending': True,
            'per_page': 100
        }
    )
    assert expected_call == session.last_call
    assert len(samples) == len(gems)
    for i in range(len(gems)):
        assert samples[i]['uids']['id'] == gems[i].uids['id']


def test_register(gemd_collection):
    """Check that register routes to the correct collections"""
    targets = [
        MaterialTemplate("foo"),
        MaterialSpec("foo"),
        MaterialRun("foo"),
        ProcessTemplate("foo"),
        ProcessSpec("foo"),
        ProcessRun("foo"),
        MeasurementTemplate("foo"),
        MeasurementSpec("foo"),
        MeasurementRun("foo"),
        IngredientSpec("foo"),
        IngredientRun(),
        PropertyTemplate("bar", bounds=IntegerBounds(0, 1)),
        ParameterTemplate("bar", bounds=IntegerBounds(0, 1)),
        ConditionTemplate("bar", bounds=IntegerBounds(0, 1))
    ]

    for obj in targets:
        assert len(obj.uids) == 0
        gemd_collection.register(obj, dry_run=True)
        assert len(obj.uids) == 0
        registered = gemd_collection.register(obj, dry_run=False)
        assert len(obj.uids) == 1
        assert len(registered.uids) == 1
        assert basename(gemd_collection.session.calls[-1].path) == basename(gemd_collection._path_template)
        for pair in obj.uids.items():
            assert pair[1] == registered.uids[pair[0]]


def test_register_no_mutate(gemd_collection):
    """Check that register routes to the correct collections"""
    expected = {
        MaterialTemplateCollection: MaterialTemplate("foo",
                                                     uids={'scope1': 'A',
                                                           'scope2': 'B'
                                                           }
                                                     ),
        MaterialSpecCollection: MaterialSpec("foo",
                                             uids={'id': str(uuid4())}
                                             ),
    }
    for specific_collection, obj in expected.items():
        len_before = len(obj.uids)
        registered = gemd_collection.register(obj)
        assert len(obj.uids) == len_before
        for pair in registered.uids.items():
            assert pair[1] == obj.uids.get(pair[0], 'No such key')


def test_register_all(gemd_collection):
    """Check that register_all registers everything and routes to all collections"""
    bounds = IntegerBounds(0, 1)
    property_template = PropertyTemplate("bar", bounds=bounds)
    parameter_template = ParameterTemplate("bar", bounds=bounds)
    condition_template = ConditionTemplate("bar", bounds=bounds)
    foo_process_template = ProcessTemplate("foo",
                                           conditions=[[condition_template, bounds]],
                                           parameters=[[parameter_template, bounds]])

    foo_process_spec = ProcessSpec("foo", template=foo_process_template)
    foo_process_run = ProcessRun("foo", spec=foo_process_spec)
    foo_material_template = MaterialTemplate("foo", properties=[[property_template, bounds]])
    foo_material_spec = MaterialSpec("foo", template=foo_material_template, process=foo_process_spec)
    foo_material_run = MaterialRun("foo", spec=foo_material_spec, process=foo_process_run)
    foo_measurement_template = MeasurementTemplate("foo",
                                                   conditions=[[condition_template, bounds]],
                                                   parameters=[[parameter_template, bounds]],
                                                   properties=[[property_template, bounds]])
    foo_measurement_spec = MeasurementSpec("foo", template=foo_measurement_template)
    foo_measurement_run = MeasurementRun("foo", spec=foo_measurement_spec, material=foo_material_run)

    baz_process_template = ProcessTemplate("baz",
                                           conditions=[[condition_template, bounds]],
                                           parameters=[[parameter_template, bounds]])
    baz_process_spec = ProcessSpec("baz", template=baz_process_template)
    baz_process_run = ProcessRun("baz", spec=baz_process_spec)
    baz_material_template = MaterialTemplate("baz", properties=[[property_template, bounds]])
    baz_material_spec = MaterialSpec("baz", template=baz_material_template, process=baz_process_spec)
    baz_material_run = MaterialRun("baz", spec=baz_material_spec, process=baz_process_run)
    baz_measurement_template = MeasurementTemplate("baz",
                                                   conditions=[[condition_template, bounds]],
                                                   parameters=[[parameter_template, bounds]],
                                                   properties=[[property_template, bounds]])
    baz_measurement_spec = MeasurementSpec("baz", template=baz_measurement_template)
    baz_measurement_run = MeasurementRun("baz", spec=baz_measurement_spec, material=baz_material_run)

    foo_baz_ingredient_spec = IngredientSpec("foo", material=foo_material_spec, process=baz_process_spec)
    foo_baz_ingredient_run = IngredientRun(spec=foo_baz_ingredient_spec, material=foo_material_run, process=baz_process_run)

    expected = [
        foo_baz_ingredient_run,
        foo_baz_ingredient_spec,
        foo_measurement_run,
        foo_measurement_spec,
        foo_measurement_template,
        foo_material_run,
        foo_material_spec,
        foo_material_template,
        foo_process_run,
        foo_process_spec,
        foo_process_template,

        baz_measurement_run,
        baz_measurement_spec,
        baz_measurement_template,
        baz_material_run,
        baz_material_spec,
        baz_material_template,
        baz_process_run,
        baz_process_spec,
        baz_process_template,

        property_template,
        parameter_template,
        condition_template
    ]

    for obj in expected:
        assert len(obj.uids) == 0  # All should be without ids

    # dry_run should pass for all objects and shouldn't mutate the objects
    gemd_collection.register_all(expected, dry_run=True)

    for obj in expected:
        assert len(obj.uids) == 0  # All should be without ids
    registered = gemd_collection.register_all(expected)
    assert len(registered) == len(expected)
    for x in expected:
        assert x in registered
    for x in registered:
        assert x in expected

    seen_ids = set()
    for obj in expected:
        assert len(obj.uids) == 1  # All should now have exactly 1 id
        for pair in obj.uids.items():
            assert pair not in seen_ids  # All ids are different
            seen_ids.add(pair)
    for obj in registered:
        for pair in obj.uids.items():
            assert pair in seen_ids  # registered items have the same ids

    assert gemd_collection.register_all([]) == [], "Trouble with an empty list."


def test_register_all_dry_run(gemd_collection):
    """Verify expected behavior around batching.  Note we cannot actually test dependencies."""
    from gemd.demo.cake import make_cake_templates, make_cake_spec, make_cake, change_scope
    from gemd.util import flatten

    change_scope("pr-688")
    tmpl = make_cake_templates()
    spec = make_cake_spec(tmpl=tmpl)
    lst = [make_cake(tmpl=tmpl, cake_spec=spec) for _ in range(1)]

    all_of_em = flatten(lst)

    objects = []
    templates = []
    for x in all_of_em:
        if "pr-688-template" in x.uids:
            if x not in templates:
                templates.append(x)
        else:
            if x not in objects:
                objects.append(x)

    result_all = gemd_collection.register_all(all_of_em, dry_run=True)
    for x in all_of_em:
        assert x in result_all
    result_obj = gemd_collection.register_all(objects, dry_run=True)
    for x in templates:
        assert x not in result_obj
    for x in objects:
        assert x in result_obj


def test_register_all_object_update(gemd_collection):
    """Check that uids of gemd-python objects get updated"""
    process = GemdProcessSpec("process")
    material = GemdMaterialSpec("material", process=process)

    registered_process, registered_material = gemd_collection.register_all([process, material])

    assert process.uids == registered_process.uids
    assert material.uids == registered_material.uids


def test_delete(gemd_collection, session):
    """
    Check that delete routes to the correct collections
    and works when passed a data object or a UUID representation.

    """
    targets = [
        MaterialTemplate("foo", uids={CITRINE_SCOPE: str(uuid4())}),
        MaterialSpec("foo", uids={CITRINE_SCOPE: str(uuid4())}),
        MaterialRun("foo", uids={CITRINE_SCOPE: str(uuid4())}),
        ProcessTemplate("foo", uids={CITRINE_SCOPE: str(uuid4())}),
    ]

    for obj in targets:
        for dry_run in True, False:
            session.set_response(obj.dump())  # Delete calls get, must return object data internally
            gemd_collection.delete(obj, dry_run=dry_run)
            assert gemd_collection.session.calls[-1].path.split("/")[-3] == basename(gemd_collection._path_template)

            # And again, with uids
            session.set_response(obj.dump())  # Delete calls get, must return object data internally
            gemd_collection.delete(obj.uid, dry_run=dry_run)
            assert gemd_collection.session.calls[-1].path.split("/")[-3] == basename(gemd_collection._path_template)


def test_update(gemd_collection):
    """Check that updating a template calls the same path as register, but a warning is thrown."""
    template = MaterialTemplate("to be updated")
    template = gemd_collection.register(template)
    template.description = "updated description"
    template_updated = gemd_collection.update(template)
    assert template_updated == template
    assert gemd_collection.session.calls[0].path == gemd_collection.session.calls[1].path


def test_async_update(gemd_collection, session):
    """Check that async update returns appropriately returns None on success."""
    obj = ProcessTemplate(
        "foo",
        uids={'id': str(uuid4())}
    )
    fake_job_status_resp = {
        'job_type': 'some_typ',
        'status': 'Success',
        'tasks': [],
        'output': {}
    }

    session.set_responses(JobSubmissionResponseFactory(), fake_job_status_resp)

    # This returns None on successful update with wait.
    gemd_collection.async_update(obj, wait_for_response=True)


def test_async_update_and_no_dataset_id(gemd_collection, session):
    """Ensure async_update requires a dataset id"""

    obj = ProcessTemplate(
        "foo",
        uids={'id': str(uuid4())}
    )

    session.set_response(JobSubmissionResponseFactory())
    gemd_collection.dataset_id = None

    with pytest.raises(RuntimeError):
        gemd_collection.async_update(obj, wait_for_response=False)


def test_async_update_timeout(gemd_collection, session):
    """Ensure the proper exception is thrown on a timeout error"""

    obj = ProcessTemplate(
        "foo",
        uids={'id': str(uuid4())}
    )
    fake_job_status_resp = {
        'job_type': 'some_typ',
        'status': 'Pending',
        'tasks': [],
        'output': {}
    }

    session.set_responses(JobSubmissionResponseFactory(), fake_job_status_resp)

    with pytest.raises(PollingTimeoutError):
        gemd_collection.async_update(obj, wait_for_response=True,
                                               timeout=-1.0)


def test_async_update_and_wait(gemd_collection, session):
    """Check that async_update parses the response when waiting"""

    obj = ProcessTemplate(
        "foo",
        uids={'id': str(uuid4())}
    )
    fake_job_status_resp = {
        'job_type': 'some_typ',
        'status': 'Success',
        'tasks': [],
        'output': {}
    }

    session.set_responses(JobSubmissionResponseFactory(), fake_job_status_resp)

    # This returns None on successful update with wait.
    gemd_collection.async_update(obj, wait_for_response=True)


def test_async_update_and_wait_failure(gemd_collection, session):
    """Check that async_update parses the failure correctly"""

    obj = ProcessTemplate(
        "foo",
        uids={'id': str(uuid4())}
    )
    fake_job_status_resp = {
        'job_type': 'some_typ',
        'status': 'Failure',
        'tasks': [],
        'output': {}
    }

    session.set_responses(JobSubmissionResponseFactory(), fake_job_status_resp)

    with pytest.raises(JobFailureError):
        gemd_collection.async_update(obj, wait_for_response=True)


def test_async_update_with_no_wait(gemd_collection, session):
    """Check that async_update parses the response when not waiting"""

    obj = ProcessTemplate(
        "foo",
        uids={'id': str(uuid4())}
    )

    session.set_response(JobSubmissionResponseFactory())
    job_id = gemd_collection.async_update(obj, wait_for_response=False)
    assert job_id is not None


def test_batch_delete(gemd_collection, session):
    job_resp = {
        'job_id': '1234'
    }

    import json
    failures_escaped_json = json.dumps([
        {
            "id":{
                'scope': 'somescope',
                'id': 'abcd-1234'
            },
            'cause': {
                "code": 400,
                "message": "",
                "validation_errors": [
                    {
                        "failure_message": "fail msg",
                        "failure_id": "identifier.coreid.missing"
                    }
                ]
            }
        }
    ])

    failed_job_resp = {
        'job_type': 'batch_delete',
        'status': 'Success',
        'tasks': [],
        'output': {
            'failures': failures_escaped_json
        }
    }

    session.set_responses(job_resp, failed_job_resp)

    # When
    del_resp = gemd_collection.batch_delete([UUID(
        '16fd2706-8baf-433b-82eb-8c7fada847da')])

    # Then
    assert 2 == session.num_calls

    assert len(del_resp) == 1
    first_failure = del_resp[0]

    expected_api_error = ApiError(400, "",
                                  validation_errors=[ValidationError(
                                      failure_message="fail msg",
                                      failure_id="identifier.coreid.missing")])

    assert first_failure == (LinkByUID('somescope', 'abcd-1234'), expected_api_error)


def test_batch_delete_bad_input(gemd_collection):
    with pytest.raises(TypeError):
        gemd_collection.batch_delete([False])


def test_type_passthrough(gemd_collection, session):
    """Verify objects that are not directly referenced by objects (e.g., a tuple of Templates) don't get type information stripped."""
    # Generate some metadata
    metadata = {
        'dataset': str(uuid4()),
        'audit_info': AuditInfo.build({"created_by": str(uuid4()),
                                       "created_at": 1559933807392
                                       }),
        "tags": [f"{CITRINE_TAG_PREFIX}::added"]
    }
    # Set up the Condition Templates
    low_tmpl, high_tmpl = [
        ConditionTemplate('condition low', uids={CITRINE_SCOPE: str(uuid4())}, bounds=IntegerBounds(1, 10)),
        ConditionTemplate('condition high', uids={CITRINE_SCOPE: str(uuid4())}, bounds=IntegerBounds(11, 20)),
    ]
    session.set_response({"objects": [dict(low_tmpl.dump(), **metadata),
                                      dict(high_tmpl.dump(), **metadata),
                                      ]})
    low_tmpl, high_tmpl = gemd_collection.register_all([low_tmpl, high_tmpl])
    assert low_tmpl.dataset is not None
    assert low_tmpl.audit_info is not None
    assert high_tmpl.dataset is not None
    assert high_tmpl.audit_info is not None

    ptempl = ProcessTemplate(
        'my template',
        uids={CITRINE_SCOPE: str(uuid4())},
        conditions=[(low_tmpl, IntegerBounds(2, 4)), (high_tmpl, IntegerBounds(12, 15))],

    )
    session.set_response(dict(ptempl.dump(), **metadata))
    ptempl = gemd_collection.register(ptempl)
    assert ptempl.dataset is not None
    assert ptempl.audit_info is not None

    arr = [
        ProcessSpec(
            'foo',
            uids={CITRINE_SCOPE: str(uuid4())},
            template=ptempl,
            conditions=[
                Condition(name='low', value=NominalInteger(3), template=low_tmpl),
                Condition(name='high', value=NominalInteger(13), template=high_tmpl),
            ]
        ),
        ProcessSpec(
            'bar',
            uids={CITRINE_SCOPE: str(uuid4())},
            template=ptempl,
            conditions=[
                Condition(name='high', value=NominalInteger(14), template=high_tmpl),
            ]
        ),
        ProcessSpec('baz', uids={CITRINE_SCOPE: str(uuid4())}),
    ]
    session.set_response({"objects": [dict(x.dump(), **metadata) for x in arr]})
    pspecs = gemd_collection.register_all(arr)
    assert([s.name for s in pspecs] == ['foo', 'bar', 'baz'])
    assert pspecs == arr


def test_tag_magic(gemd_collection, session):
    auto_tag = f"{CITRINE_TAG_PREFIX}::added"
    additions = {"tags": ["tag", auto_tag],
                 "uids": {CITRINE_SCOPE: str(uuid4()),
                          "original": "id"
                          }
                 }

    obj1 = ProcessSpec("one", tags=["tag"], uids={"original": "id"})
    session.set_response(dict(obj1.dump(), **additions))
    res1 = gemd_collection.register(obj1)
    assert obj1 == res1
    assert auto_tag in obj1.tags

    obj2 = ProcessSpec("two", tags=["tag"], uids={"original": "id"})
    session.set_response({"objects": [dict(obj2.dump(), **additions)]})
    res2 = gemd_collection.register_all([obj2])
    assert obj2 == res2[0]
    assert auto_tag in obj2.tags

    obj3 = ProcessSpec("one", tags=["tag"], uids={"original": "id"})
    session.set_response(dict(obj3.dump(), **additions))
    res3 = gemd_collection.register(obj3, dry_run=True)
    assert obj3 == res3
    assert auto_tag not in obj3.tags

    obj4 = ProcessSpec("two", tags=["tag"], uids={"original": "id"})
    session.set_response({"objects": [dict(obj4.dump(), **additions)]})
    res4 = gemd_collection.register_all([obj4], dry_run=True)
    assert obj4 == res4[0]
    assert auto_tag not in obj4.tags
