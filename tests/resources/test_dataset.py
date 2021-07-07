import uuid
from os.path import basename
from uuid import UUID, uuid4

import pytest
from gemd.entity.bounds.integer_bounds import IntegerBounds
from gemd.entity.link_by_uid import LinkByUID

from citrine.exceptions import PollingTimeoutError, JobFailureError, NotFound
from citrine.resources.api_error import ApiError, ValidationError
from citrine.resources.condition_template import ConditionTemplateCollection, ConditionTemplate
from citrine.resources.dataset import DatasetCollection
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


def test_gemd_resource_get_project_id(dataset):
    assert dataset.project_id == dataset.gemd.project_id


def test_files_get_project_id(dataset):
    assert dataset.project_id == dataset.files.project_id


def test_gemd_posts(dataset):
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
        PropertyTemplateCollection: PropertyTemplate("bar", bounds=IntegerBounds(0, 1)),
        ParameterTemplateCollection: ParameterTemplate("bar", bounds=IntegerBounds(0, 1)),
        ConditionTemplateCollection: ConditionTemplate("bar", bounds=IntegerBounds(0, 1))
    }

    for collection, obj in expected.items():
        obj.name = 'This is my name'

        # Register the objects
        assert len(obj.uids) == 0
        registered = dataset.register(obj)
        assert len(obj.uids) == 1
        assert len(registered.uids) == 1
        assert basename(dataset.session.calls[-1].path) == basename(collection._path_template)
        for pair in obj.uids.items():
            assert pair[1] == registered.uids[pair[0]]

        # Update the objects
        registered.name = 'Name change!'
        updated = dataset.update(registered)
        assert registered.name == updated.name
        assert len(updated.uids) == 1
        for pair in registered.uids.items():
            assert pair[1] == updated.uids[pair[0]]

        # Delete them all
        dataset.delete(updated)
        assert dataset.session.calls[-1].path.split("/")[-3] == basename(collection._path_template)

    # Register all
    before = list(expected.values())
    seen_ids = set()
    for obj in before:
        for pair in obj.uids.items():
            assert pair not in seen_ids  # All ids are different
            seen_ids.add(pair)

    after = dataset.register_all(before)
    assert len(before) == len(after)
    for obj in after:
        for pair in obj.uids.items():
            assert pair in seen_ids  # registered items have the same ids


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


def test_batch_delete(dataset):
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

    session = dataset.session
    session.set_responses(job_resp, failed_job_resp)

    # When
    del_resp = dataset.gemd_batch_delete([uuid.UUID(
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


def test_batch_delete_bad_input(dataset):
    with pytest.raises(TypeError):
        dataset.gemd_batch_delete([False])


def test_delete_contents_ok(dataset):

    job_resp = {
        'job_id': '1234'
    }

    failed_job_resp = {
        'job_type': 'batch_delete',
        'status': 'Success',
        'tasks': [],
        'output': {
            # Keep in mind this is a stringified JSON value. Eww.
            'failures': '[]'
        }
    }

    session = dataset.session
    session.set_responses(job_resp, failed_job_resp)

    # When
    del_resp = dataset.delete_contents()

    # Then
    assert len(del_resp) == 0

    # Ensure we made the expected delete call
    expected_call = FakeCall(
        method='DELETE',
        path='projects/{}/datasets/{}/contents'.format(dataset.project_id, dataset.uid)
    )
    assert len(session.calls) == 2
    assert session.calls[0] == expected_call
