import uuid
from os.path import basename
from uuid import UUID, uuid4

import pytest
from gemd.entity.bounds.integer_bounds import IntegerBounds
from gemd.entity.link_by_uid import LinkByUID
from gemd.entity.object.material_spec import MaterialSpec as GemdMaterialSpec
from gemd.entity.object.process_spec import ProcessSpec as GemdProcessSpec

from citrine.exceptions import PollingTimeoutError, JobFailureError, NotFound
from citrine.resources.api_error import ApiError, ValidationError
from citrine.resources.condition_template import ConditionTemplateCollection, ConditionTemplate
from citrine.resources.dataset import DatasetCollection
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
from tests.utils.factories import DatasetDataFactory, DatasetFactory
from tests.utils.factories import JobSubmissionResponseFactory
from tests.utils.session import FakeSession, FakePaginatedSession, FakeCall


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def paginated_session() -> FakePaginatedSession:
    return FakePaginatedSession()


@pytest.fixture
def collection(session) -> DatasetCollection:
    return DatasetCollection(
        project_id=UUID('6b608f78-e341-422c-8076-35adc8828545'),
        session=session
    )


@pytest.fixture
def paginated_collection(paginated_session) -> DatasetCollection:
    return DatasetCollection(
        project_id=UUID('6b608f78-e341-422c-8076-35adc8828545'),
        session=paginated_session
    )


@pytest.fixture(scope="function")
def dataset():
    dataset = DatasetFactory(name='Test Dataset')
    dataset.project_id = UUID('6b608f78-e341-422c-8076-35adc8828545')
    dataset.uid = UUID("503d7bf6-8e2d-4d29-88af-257af0d4fe4a")
    dataset.session = FakeSession()

    return dataset


def test_register_dataset(collection, session):
    # Given
    name = 'Test Dataset'
    summary = 'testing summary'
    description = 'testing description'
    session.set_response(DatasetDataFactory(name=name, summary=summary, description=description))

    # When
    dataset = collection.register(DatasetFactory(name=name, summary=summary, description=description))

    expected_call = FakeCall(
        method='POST',
        path='projects/{}/datasets'.format(collection.project_id),
        json={'name': name, 'summary': summary, 'description': description}
    )
    assert session.num_calls == 1
    assert expected_call == session.last_call
    assert name == dataset.name


def test_register_dataset_with_idempotent_put(collection, session):
    # Given
    name = 'Test Dataset'
    summary = 'testing summary'
    description = 'testing description'
    unique_name = 'foo'
    session.set_response(DatasetDataFactory(name=name, summary=summary, description=description, unique_name=unique_name))

    # When
    session.use_idempotent_dataset_put = True
    dataset = collection.register(DatasetFactory(name=name, summary=summary, description=description, unique_name=unique_name))

    expected_call = FakeCall(
        method='PUT',
        path='projects/{}/datasets'.format(collection.project_id),
        json={'name': name, 'summary': summary, 'description': description, 'unique_name': unique_name}
    )
    assert session.num_calls == 1
    assert expected_call == session.last_call
    assert name == dataset.name


def test_register_dataset_with_existing_id(collection, session):
    # Given
    name = 'Test Dataset'
    summary = 'testing summary'
    description = 'testing description'
    session.set_response(DatasetDataFactory(name=name, summary=summary, description=description))

    # When
    dataset = DatasetFactory(name=name, summary=summary,
                   description=description)

    ds_uid = UUID('cafebeef-e341-422c-8076-35adc8828545')
    dataset.uid = ds_uid
    dataset = collection.register(dataset)

    expected_call = FakeCall(
        method='PUT',
        path='projects/{}/datasets/{}'.format(collection.project_id, ds_uid),
        json={'name': name, 'summary': summary, 'description': description,
              'id': str(ds_uid)}
    )
    assert session.num_calls == 1
    assert expected_call == session.last_call
    assert name == dataset.name


def test_get_by_unique_name_with_single_result(collection, session):
    # Given
    name = 'Test Dataset'
    unique_name = "foo"
    session.set_response([DatasetDataFactory(name=name, unique_name=unique_name)])

    # When
    result_ds = collection.get_by_unique_name(unique_name)

    # Then
    expected_call = FakeCall(
        method='GET',
        path='projects/{}/datasets?unique_name={}'.format(collection.project_id, unique_name)
    )
    assert session.num_calls == 1
    assert expected_call == session.last_call
    assert result_ds.name == name
    assert result_ds.unique_name == unique_name


def test_get_by_unique_name_with_no_result(collection, session):
    # Given
    session.set_response([])

    # When
    with pytest.raises(NotFound):
        collection.get_by_unique_name("unimportant")


def test_get_by_unique_name_no_unique_name_present(collection, session):
    # When
    with pytest.raises(ValueError):
        collection.get_by_unique_name(None)

def test_get_by_unique_name_multiple_results(collection, session):

    # This really shouldn't happen

    # Given
    session.set_response([DatasetDataFactory(), DatasetDataFactory()])

    # When
    with pytest.raises(RuntimeError):
        collection.get_by_unique_name("blah")


def test_list_datasets(paginated_collection, paginated_session):
    # Given
    datasets_data = DatasetDataFactory.create_batch(50)
    paginated_session.set_response(datasets_data)

    # When
    datasets = list(paginated_collection.list(per_page=20))

    # Then
    assert 3 == paginated_session.num_calls
    expected_first_call = FakeCall(method='GET', path='projects/{}/datasets'.format(paginated_collection.project_id),
                                   params={'per_page': 20})
    expected_last_call = FakeCall(method='GET', path='projects/{}/datasets'.format(paginated_collection.project_id),
                                  params={'page': 3, 'per_page': 20})
    assert expected_first_call == paginated_session.calls[0]
    assert expected_last_call == paginated_session.last_call
    assert 50 == len(datasets)

    expected_uids = [d['id'] for d in datasets_data]
    dataset_ids = [str(d.uid) for d in datasets]
    assert dataset_ids == expected_uids


def test_list_datasets_infinite_loop_detect(paginated_collection, paginated_session):
    # Given
    batch_size = 100
    datasets_data = DatasetDataFactory.create_batch(batch_size)
    # duplicate the data, this simulates an API that keeps returning the first page
    datasets_data.extend(datasets_data)
    paginated_session.set_response(datasets_data)

    # When
    datasets = list(paginated_collection.list(per_page=batch_size))

    # Then
    assert 2 == paginated_session.num_calls  # duplicate UID detected on the second call
    expected_first_call = FakeCall(method='GET', path='projects/{}/datasets'.format(paginated_collection.project_id),
                                   params={'per_page': batch_size})
    expected_last_call = FakeCall(method='GET', path='projects/{}/datasets'.format(paginated_collection.project_id),
                                  params={'page': 2, 'per_page': batch_size})
    assert expected_first_call == paginated_session.calls[0]
    assert expected_last_call == paginated_session.last_call
    assert len(datasets) == batch_size

    expected_uids = [d['id'] for d in datasets_data[0:batch_size]]
    dataset_ids = [str(d.uid) for d in datasets]
    assert dataset_ids == expected_uids


def test_delete_dataset(collection, session, dataset):
    # Given
    uid = str(uuid4())

    # When
    collection.delete(uid)

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(method='DELETE', path='projects/{}/datasets/{}'.format(
        collection.project_id, uid))
    assert expected_call == session.last_call


def test_string_representation(dataset):
    assert "<Dataset 'Test Dataset'>" == str(dataset)


def test_property_templates_get_project_id(dataset):
    assert dataset.project_id == dataset.property_templates.project_id


def test_condition_templates_get_project_id(dataset):
    assert dataset.project_id == dataset.condition_templates.project_id


def test_parameter_templates_get_project_id(dataset):
    assert dataset.project_id == dataset.parameter_templates.project_id


def test_material_templates_get_project_id(dataset):
    assert dataset.project_id == dataset.material_templates.project_id


def test_measurement_templates_get_project_id(dataset):
    assert dataset.project_id == dataset.measurement_templates.project_id


def test_process_templates_get_project_id(dataset):
    assert dataset.project_id == dataset.process_templates.project_id


def test_process_runs_get_project_id(dataset):
    assert dataset.project_id == dataset.process_runs.project_id


def test_measurement_runs_get_project_id(dataset):
    assert dataset.project_id == dataset.measurement_runs.project_id


def test_material_runs_get_project_id(dataset):
    assert dataset.project_id == dataset.material_runs.project_id


def test_ingredient_runs_get_project_id(dataset):
    assert dataset.project_id == dataset.ingredient_runs.project_id


def test_process_specs_get_project_id(dataset):
    assert dataset.project_id == dataset.process_specs.project_id


def test_measurement_specs_get_project_id(dataset):
    assert dataset.project_id == dataset.measurement_specs.project_id


def test_material_specs_get_project_id(dataset):
    assert dataset.project_id == dataset.material_specs.project_id


def test_ingredient_specs_get_project_id(dataset):
    assert dataset.project_id == dataset.ingredient_specs.project_id


def test_files_get_project_id(dataset):
    assert dataset.project_id == dataset.files.project_id


def test_register_data_concepts(dataset):
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

    for collection, obj in expected.items():
        assert len(obj.uids) == 0
        registered = dataset.register(obj)
        assert len(obj.uids) == 1
        assert len(registered.uids) == 1
        assert basename(dataset.session.calls[-1].path) == basename(collection._path_template)
        for pair in obj.uids.items():
            assert pair[1] == registered.uids[pair[0]]


def test_update(dataset):
    """Check that updating a template calls the same path as register, but a warning is thrown."""
    template = MaterialTemplate("to be updated")
    template = dataset.register(template)
    template.description = "updated description"
    with pytest.warns(UserWarning):
        template_updated = dataset.update(template)
    assert template_updated == template
    assert dataset.session.calls[0].path == dataset.session.calls[1].path


def test_register_data_concepts_no_mutate(dataset):
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
    for collection, obj in expected.items():
        len_before = len(obj.uids)
        registered = dataset.register(obj)
        assert len(obj.uids) == len_before
        for pair in registered.uids.items():
            assert pair[1] == obj.uids.get(pair[0], 'No such key')


def test_async_update_and_wait(dataset, session):
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

    dataset.session.set_responses(JobSubmissionResponseFactory(), fake_job_status_resp)

    # This returns None on successful update with wait.
    dataset.process_templates.async_update(obj, wait_for_response=True)


def test_async_update_and_wait_failure(dataset, session):
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

    dataset.session.set_responses(JobSubmissionResponseFactory(), fake_job_status_resp)

    with pytest.raises(JobFailureError):
        dataset.process_templates.async_update(obj, wait_for_response=True)


def test_async_update_with_no_wait(dataset, session):
    """Check that async_update parses the response when not waiting"""

    obj = ProcessTemplate(
        "foo",
        uids={'id': str(uuid4())}
    )

    dataset.session.set_response(JobSubmissionResponseFactory())
    job_id = dataset.process_templates.async_update(obj, wait_for_response=False)
    assert job_id is not None


def test_async_update_and_no_dataset_id(dataset, session):
    """Ensure async_update requires a dataset id"""

    obj = ProcessTemplate(
        "foo",
        uids={'id': str(uuid4())}
    )

    dataset.session.set_response(JobSubmissionResponseFactory())
    dataset.uid = None

    with pytest.raises(RuntimeError):
        dataset.process_templates.async_update(obj, wait_for_response=False)


def test_async_update_timeout(dataset, session):
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

    dataset.session.set_responses(JobSubmissionResponseFactory(), fake_job_status_resp)

    with pytest.raises(PollingTimeoutError):
        dataset.process_templates.async_update(obj, wait_for_response=True,
                                                              timeout=-1.0)


def test_register_all_data_concepts(dataset):
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
    registered = dataset.register_all(expected.keys())
    assert len(registered) == len(expected)

    seen_ids = set()
    for obj in expected:
        assert len(obj.uids) == 1  # All should now have exactly 1 id
        for pair in obj.uids.items():
            assert pair not in seen_ids  # All ids are different
            seen_ids.add(pair)
    for obj in registered:
        for pair in obj.uids.items():
            assert pair in seen_ids  # registered items have the same ids

    call_basenames = [call.path.split('/')[-2] for call in dataset.session.calls]
    collection_basenames = [basename(collection._path_template) for collection in expected.values()]
    assert set(call_basenames) == set(collection_basenames)
    assert len(set(call_basenames)) == len(call_basenames)  # calls are batched internally

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


def test_register_all_object_update(dataset):
    """Check that uids of gemd-python objects get updated"""
    process = GemdProcessSpec("process")
    material = GemdMaterialSpec("material", process=process)

    registered_process, registered_material = dataset.register_all([process, material])

    assert process.uids == registered_process.uids
    assert material.uids == registered_material.uids


def test_delete_data_concepts(dataset):
    """Check that delete routes to the correct collections"""
    expected = {
        MaterialTemplateCollection: MaterialTemplate("foo", uids={"foo": "bar"}),
        MaterialSpecCollection: MaterialSpec("foo", uids={"foo": "bar"}),
        MaterialRunCollection: MaterialRun("foo", uids={"foo": "bar"}),
        ProcessTemplateCollection: ProcessTemplate("foo", uids={"foo": "bar"}),
    }

    for collection, obj in expected.items():
        dataset.delete(obj)
        assert dataset.session.calls[-1].path.split("/")[-3] == basename(collection._path_template)


def test_delete_missing_uid(dataset):
    """Check that delete raises an error when there are no uids"""
    obj = MaterialTemplate("foo")
    with pytest.raises(ValueError):
        dataset.delete(obj)

def test_batch_delete(dataset):
    failure_resp = {'failures': [
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
    ]}

    session = dataset.session
    session.set_responses(failure_resp, failure_resp)

    # When
    del_resp = dataset.gemd_batch_delete([uuid.UUID(
        '16fd2706-8baf-433b-82eb-8c7fada847da')])

    # Then
    assert 1 == session.num_calls
    expect_call = FakeCall(
        method="POST",
        path="/projects/{}/gemd/batch-delete".format(dataset.project_id)
    )
    assert expect_call.method == session.last_call.method
    assert expect_call.path == session.last_call.path

    assert len(del_resp) == 1
    first_failure = del_resp[0]

    expected_api_error = ApiError(400, "",
                                  validation_errors=[ValidationError(
                                      failure_message="fail msg",
                                      failure_id="identifier.coreid.missing")])


    assert first_failure == (LinkByUID('somescope', 'abcd-1234'), expected_api_error)

    # And again with tuples of (scope, id)
    del_resp = dataset.gemd_batch_delete([LinkByUID('id',
                                                    '16fd2706-8baf-433b-82eb-8c7fada847da')])
    assert len(del_resp) == 1
    first_failure = del_resp[0]

    assert first_failure == (LinkByUID('somescope', 'abcd-1234'), expected_api_error)


def test_batch_delete_bad_input(dataset):
    with pytest.raises(TypeError):
        dataset.gemd_batch_delete(['hiya!'])