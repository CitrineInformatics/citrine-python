import random
from uuid import uuid4, UUID
from os.path import basename

import pytest

from gemd.entity.bounds.integer_bounds import IntegerBounds
from gemd.entity.link_by_uid import LinkByUID
from gemd.entity.object.material_spec import MaterialSpec as GemdMaterialSpec
from gemd.entity.object.process_spec import ProcessSpec as GemdProcessSpec

from citrine.exceptions import PollingTimeoutError, JobFailureError, NotFound
from citrine.resources.api_error import ApiError, ValidationError
from citrine.resources.condition_template import ConditionTemplateCollection, ConditionTemplate
from citrine.resources.data_concepts import DataConcepts
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
    expected = {
        MaterialTemplateCollection: MaterialTemplate("foo"),
        MaterialSpecCollection: MaterialSpec("foo"),
        MaterialRunCollection: MaterialRun("foo"),
        ProcessTemplateCollection: ProcessTemplate("foo"),
        ProcessSpecCollection: ProcessSpec("foo"),
        ProcessRunCollection: ProcessRun("foo"),
        MeasurementTemplateCollection: MeasurementTemplate("foo"),
        MeasurementSpecCollection: MeasurementSpec("foo"),
        MeasurementRunCollection: MeasurementRun("foo"),
        IngredientSpecCollection: IngredientSpec("foo"),
        IngredientRunCollection: IngredientRun(),
        PropertyTemplateCollection: PropertyTemplate("bar", bounds=IntegerBounds(0, 1)),
        ParameterTemplateCollection: ParameterTemplate("bar", bounds=IntegerBounds(0, 1)),
        ConditionTemplateCollection: ConditionTemplate("bar", bounds=IntegerBounds(0, 1))
    }

    for specific_collection, obj in expected.items():
        assert len(obj.uids) == 0
        gemd_collection.register(obj, dry_run=True)
        assert len(obj.uids) == 0
        registered = gemd_collection.register(obj, dry_run=False)
        assert len(obj.uids) == 1
        assert len(registered.uids) == 1
        assert basename(gemd_collection.session.calls[-1].path) == basename(specific_collection._path_template)
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
    baz_template = MaterialTemplate("baz")
    foo_measurement_template = MeasurementTemplate("foo",
                                                   conditions=[[condition_template, bounds]],
                                                   parameters=[[parameter_template, bounds]],
                                                   properties=[[property_template, bounds]])
    foo_measurement_spec = MeasurementSpec("foo", template=foo_measurement_template)
    foo_measurement_run = MeasurementRun("foo", spec=foo_measurement_spec, material=foo_material_run)
    foo_ingredient_spec = IngredientSpec("foo", material=foo_material_spec, process=foo_process_spec)
    foo_ingredient_run = IngredientRun(spec=foo_ingredient_spec, material=foo_material_run, process=foo_process_run)
    baz_run = MeasurementRun("baz")

    # worst order possible
    expected = {
        foo_ingredient_run: IngredientRunCollection,
        foo_ingredient_spec: IngredientSpecCollection,
        foo_measurement_run: MeasurementRunCollection,
        foo_measurement_spec: MeasurementSpecCollection,
        foo_measurement_template: MeasurementTemplateCollection,
        foo_material_run: MaterialRunCollection,
        foo_material_spec: MaterialSpecCollection,
        foo_material_template: MaterialTemplateCollection,
        foo_process_run: ProcessRunCollection,
        foo_process_spec: ProcessSpecCollection,
        foo_process_template: ProcessTemplateCollection,
        baz_template: MaterialTemplateCollection,
        baz_run: MeasurementRunCollection,
        property_template: PropertyTemplateCollection,
        parameter_template: ParameterTemplateCollection,
        condition_template: ConditionTemplateCollection
    }

    for obj in expected:
        assert len(obj.uids) == 0  # All should be without ids

    # dry_run should pass for all objects and shouldn't mutate the objects
    gemd_collection.register_all(expected.keys(), dry_run=True)

    for obj in expected:
        assert len(obj.uids) == 0  # All should be without ids
    registered = gemd_collection.register_all(expected.keys())
    assert len(registered) == len(expected)
    for x in expected:
        assert x in registered

    seen_ids = set()
    for obj in expected:
        assert len(obj.uids) == 1  # All should now have exactly 1 id
        for pair in obj.uids.items():
            assert pair not in seen_ids  # All ids are different
            seen_ids.add(pair)
    for obj in registered:
        for pair in obj.uids.items():
            assert pair in seen_ids  # registered items have the same ids

    call_basenames = [call.path.split('/')[-2] for call in gemd_collection.session.calls]
    collection_basenames = [basename(specific_collection._path_template) for specific_collection in expected.values()]
    assert set(call_basenames) == set(collection_basenames)
    assert len(set(call_basenames)) * 2 == len(call_basenames)  # calls are batched internally

    # spot check order. Does not check every constraint
    assert call_basenames.index(basename(IngredientRunCollection._path_template)) > call_basenames.index(basename(IngredientSpecCollection._path_template))
    assert call_basenames.index(basename(MaterialRunCollection._path_template)) > call_basenames.index(basename(MaterialSpecCollection._path_template))
    assert call_basenames.index(basename(MeasurementRunCollection._path_template)) > call_basenames.index(basename(MeasurementSpecCollection._path_template))
    assert call_basenames.index(basename(ProcessRunCollection._path_template)) > call_basenames.index(basename(ProcessSpecCollection._path_template))
    assert call_basenames.index(basename(MaterialSpecCollection._path_template)) > call_basenames.index(basename(MaterialTemplateCollection._path_template))
    assert call_basenames.index(basename(MeasurementSpecCollection._path_template)) > call_basenames.index(basename(MeasurementTemplateCollection._path_template))
    assert call_basenames.index(basename(ProcessSpecCollection._path_template)) > call_basenames.index(basename(ProcessTemplateCollection._path_template))
    assert call_basenames.index(basename(MaterialSpecCollection._path_template)) > call_basenames.index(basename(ProcessSpecCollection._path_template))
    assert call_basenames.index(basename(MaterialSpecCollection._path_template)) > call_basenames.index(basename(MeasurementSpecCollection._path_template))
    assert call_basenames.index(basename(MeasurementTemplateCollection._path_template)) > call_basenames.index(basename(ConditionTemplateCollection._path_template))
    assert call_basenames.index(basename(MeasurementTemplateCollection._path_template)) > call_basenames.index(basename(ParameterTemplateCollection._path_template))
    assert call_basenames.index(basename(MaterialTemplateCollection._path_template)) > call_basenames.index(basename(PropertyTemplateCollection._path_template))


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
    expected = {
        MaterialTemplateCollection: MaterialTemplate("foo", uids={"id": str(uuid4())}),
        MaterialSpecCollection: MaterialSpec("foo", uids={"id": str(uuid4())}),
        MaterialRunCollection: MaterialRun("foo", uids={"id": str(uuid4())}),
        ProcessTemplateCollection: ProcessTemplate("foo", uids={"id": str(uuid4())}),
    }

    for specific_collection, obj in expected.items():
        for dry_run in True, False:
            session.set_response(obj.dump())  # Delete calls get, must return object data internally
            gemd_collection.delete(obj, dry_run=dry_run)
            assert gemd_collection.session.calls[-1].path.split("/")[-3] == basename(specific_collection._path_template)


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
