import pytest
from uuid import uuid4, UUID

from citrine._session import Session
from citrine.exceptions import BadRequest
from citrine.resources.api_error import ValidationError
from citrine.resources.dataset import Dataset
from citrine.resources.file_link import FileLink
from citrine.resources.ingestion import (
    Ingestion, IngestionCollection, IngestionStatus, IngestionStatusType, IngestionException,
    IngestionErrorTrace, IngestionErrorType, IngestionErrorFamily, IngestionErrorLevel
)
from citrine.jobs.job import JobSubmissionResponse, JobStatusResponse, JobFailureError
from citrine.resources.project import Project

from tests.utils.factories import (
    DatasetFactory, IngestionStatusResponseDataFactory, JobSubmissionResponseDataFactory,
    JobStatusResponseDataFactory
)
from tests.utils.session import FakeCall, FakeSession, FakeRequestResponseApiError


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def dataset(session: Session):
    dataset = DatasetFactory(name='Test Dataset')
    dataset.team_id = uuid4()
    dataset.uid = uuid4()
    dataset.session = session

    return dataset


@pytest.fixture
def deprecated_dataset(session: Session):
    deprecated_dataset = DatasetFactory(name='Test Dataset')
    deprecated_dataset.uid = uuid4()
    deprecated_dataset.session = session
    deprecated_dataset.project_id = uuid4()

    return deprecated_dataset


@pytest.fixture
def collection(dataset) -> IngestionCollection:
    return dataset.ingestions


@pytest.fixture
def file_link(dataset: Dataset) -> FileLink:
    fileid = uuid4()
    url = dataset.files._get_path(uid=uuid4(), version=uuid4())
    return FileLink(filename=str(fileid), url=url)


@pytest.fixture
def ingest(collection) -> Ingestion:
    return collection.build({
        "ingestion_id": uuid4(),
        "team_id": collection.team_id,
        "dataset_id": collection.dataset_id
    })


@pytest.fixture
def operation() -> JobSubmissionResponse:
    return JobSubmissionResponse.build({
        "job_id": uuid4()
    })


@pytest.fixture
def status() -> IngestionStatus:
    return IngestionStatus.build({
        "status": IngestionStatusType.INGESTION_CREATED,
        "errors": []
    })


def test_create_deprecated_collection(session, deprecated_dataset):
    check_project = {'project': {'team': {'id': str(uuid4())}}}
    session.set_response(check_project)
    with pytest.deprecated_call():
        ingestions = deprecated_dataset.ingestions

    assert session.calls == [FakeCall(method="GET", path=f'projects/{ingestions.project_id}')]
    assert ingestions._path_template == f'projects/{ingestions.project_id}/ingestions'


def test_not_implementeds(collection):
    """Test that unimplemented methods are still that."""
    with pytest.raises(NotImplementedError):
        collection.register(operation)

    with pytest.raises(NotImplementedError):
        collection.update(operation)

    with pytest.raises(NotImplementedError):
        collection.delete(operation)

    with pytest.raises(NotImplementedError):
        collection.list()


def test_deprecation_of_positional_arguments(session):
    team_id = UUID('6b608f78-e341-422c-8076-35adc8828000')
    check_project = {'project': {'team': {'id': team_id}}}
    session.set_response(check_project)
    with pytest.deprecated_call():
        IngestionCollection(uuid4(), uuid4(), session)
    with pytest.raises(TypeError):
        IngestionCollection(project_id=uuid4(), dataset_id=uuid4(), session=None)
    with pytest.raises(TypeError):
        IngestionCollection(project_id=uuid4(), dataset_id=None, session=session)


def test_poll_for_job_completion_signature(ingest, operation, status, monkeypatch):
    """Test calls on polling."""

    outer_timeout = None
    outer_polling_delay = None
    outer_raise_errors = None

    def _mock_poll_for_job_completion(
            session,
            team_id,
            job,
            *,
            project_id=None,
            timeout=-1.0,
            polling_delay=-2.0,
            raise_errors=True):
        nonlocal outer_timeout
        nonlocal outer_polling_delay
        nonlocal outer_raise_errors
        outer_timeout = timeout
        outer_polling_delay = polling_delay
        outer_raise_errors = raise_errors

        return JobStatusResponse.build(JobStatusResponseDataFactory())

    def _mock_status(self) -> IngestionStatus:
        return status

    monkeypatch.setattr("citrine.resources.ingestion._poll_for_job_completion", _mock_poll_for_job_completion)
    monkeypatch.setattr(Ingestion, "status", _mock_status)

    ingest.poll_for_job_completion(operation)
    assert outer_timeout == -1.0
    assert outer_polling_delay == -2.0
    assert outer_raise_errors is False

    ingest.poll_for_job_completion(operation, timeout=20.0, polling_delay=5.0)
    assert outer_timeout == 20.0
    assert outer_polling_delay == 5.0
    assert outer_raise_errors is False


def test_processing_exceptions(session, ingest, monkeypatch):

    def _mock_poll_for_job_completion(**_):
        return JobStatusResponse.build(JobStatusResponseDataFactory())

    # This is mocked equivalently for all tests
    monkeypatch.setattr("citrine.resources.ingestion._poll_for_job_completion", _mock_poll_for_job_completion)
    validation_error = ValidationError.build({"failure_message": "you failed", "failure_id": "failure_id"})

    # Raise exceptions, but it worked
    ingest.raise_errors = True
    session.set_responses(
        {"job_id": str(uuid4())},
        {"status": IngestionStatusType.INGESTION_CREATED, "errors": []}
    )
    result = ingest.build_objects()
    assert result.success
    assert len(result.errors) == 0

    # Raise exceptions, and build_objects_async returned errors
    ingest.raise_errors = True
    session.set_responses(
        BadRequest("path", FakeRequestResponseApiError(400, "Bad Request", [validation_error])),
        {"status": IngestionStatusType.INGESTION_CREATED, "errors": []}
    )
    with pytest.raises(IngestionException, match="you failed"):
        ingest.build_objects()

    # Raise exceptions, and build_objects_async returned unspecified errors
    ingest.raise_errors = True
    session.set_responses(
        BadRequest("path", FakeRequestResponseApiError(400, "This has no details", [])),
        {"status": IngestionStatusType.INGESTION_CREATED, "errors": []}
    )
    with pytest.raises(IngestionException, match="no details"):
        ingest.build_objects()

    # Raise exceptions, and build_objects_async had server errors
    ingest.raise_errors = True
    session.set_responses(
        BadRequest("path", FakeRequestResponseApiError(500, "This was internal", [])),
        {"status": IngestionStatusType.INGESTION_CREATED, "errors": []}
    )
    with pytest.raises(IngestionException, match="internal"):
        ingest.build_objects()

    # Raise exceptions, and status returned errors
    ingest.raise_errors = True
    session.set_responses(
        {"job_id": str(uuid4())},
        {"status": IngestionStatusType.INGESTION_CREATED,
         "errors": [{"msg": "Bad things!",
                     "level": IngestionErrorLevel.ERROR,
                     "family": IngestionErrorFamily.STRUCTURE,
                     "error_type": IngestionErrorType.INVALID_DUPLICATE_NAME}]}
    )
    with pytest.raises(IngestionException, match="Bad things"):
        ingest.build_objects()

    # Suppress exceptions, but it worked
    ingest.raise_errors = False
    session.set_responses(
        {"job_id": str(uuid4())},
        {"status": IngestionStatusType.INGESTION_CREATED, "errors": []}
    )
    result = ingest.build_objects()
    assert result.success

    # Suppress exceptions, and build_objects_async returned errors
    ingest.raise_errors = False
    session.set_responses(
        BadRequest("path", FakeRequestResponseApiError(400, "Bad Request", [validation_error])),
        {"status": IngestionStatusType.INGESTION_CREATED,
         "errors": [{"msg": validation_error.failure_message,
                     "level": IngestionErrorLevel.ERROR,
                     "family": IngestionErrorFamily.DATA,
                     "error_type": IngestionErrorType.INVALID_DUPLICATE_NAME}]}
    )
    result = ingest.build_objects()
    assert not result.success
    assert any('you failed' in str(e) for e in result.errors)

    # Suppress exceptions, and build_objects_async returned errors
    ingest.raise_errors = False
    session.set_responses(
        BadRequest("No API error, so it's thrown", None),
        {"status": IngestionStatusType.INGESTION_CREATED,
         "errors": [IngestionErrorTrace(validation_error.failure_message).dump()]}
    )
    with pytest.raises(BadRequest):
        ingest.build_objects()

    # Suppress exceptions, and status returned errors
    ingest.raise_errors = False
    session.set_responses(
        {"job_id": str(uuid4())},
        {"status": IngestionStatusType.INGESTION_CREATED,
         "errors": [IngestionErrorTrace("Sad").dump()] * 3}
    )
    result = ingest.build_objects()
    assert not result.success
    assert any('Sad' in e.msg for e in result.errors)


def test_ingestion_with_table_build(session: FakeSession,
                                    ingest: Ingestion,
                                    dataset: Dataset,
                                    deprecated_dataset: Dataset,
                                    file_link: FileLink):
    # build_objects_async will always approve, if we get that far
    session.set_responses(JobSubmissionResponseDataFactory())

    with pytest.raises(ValueError):
        ingest.build_objects_async(build_table=True)

    with pytest.deprecated_call():
        ingest.project_id = uuid4()
    with pytest.deprecated_call():
        assert ingest.project_id is not None
    with pytest.deprecated_call():
        ingest.build_objects_async(build_table=True)
    with pytest.deprecated_call():
        ingest.project_id = None

    project_uuid = uuid4()
    project = Project("Testing", session=session, team_id=dataset.team_id)
    project.uid = project_uuid
    ingest.build_objects_async(build_table=True, project=project)
    assert session.last_call.params["project_id"] == project_uuid

    ingest.build_objects_async(build_table=True, project=project_uuid)
    assert session.last_call.params["project_id"] == project_uuid

    ingest.build_objects_async(build_table=True, project=str(project_uuid))
    assert session.last_call.params["project_id"] == project_uuid

    # full build_objects
    full_build_job = JobSubmissionResponseDataFactory()
    output = {
        'ingestion_id': str(ingest.uid),
        'gemd_table_config_version': '1',
        'table_build_job_id': str(uuid4()),
        'gemd_table_config_id': str(uuid4())
    }
    session.set_responses(
        full_build_job,
        JobStatusResponseDataFactory(
            job_id=full_build_job["job_id"],
            output=output,
        ),
        JobStatusResponseDataFactory(),
        IngestionStatusResponseDataFactory()
    )
    status = ingest.build_objects(build_table=True, project=str(project_uuid))
    assert status.success


def test_ingestion_flow(session: FakeSession,
                        ingest: Ingestion,
                        collection: IngestionCollection,
                        file_link: FileLink,
                        monkeypatch):
    validation_error = ValidationError.build({"failure_message": "I've failed"})

    with pytest.raises(ValueError, match="No files"):
        collection.build_from_file_links([])

    with pytest.raises(ValueError, match="UID"):
        collection.build_from_file_links([FileLink(filename="mine.txt", url="http:/external.com")])

    session.set_response(ingest.dump())
    assert collection.build_from_file_links([file_link]).uid == ingest.uid

    session.set_response(BadRequest("path", FakeRequestResponseApiError(400, "Sad face", [])))
    with pytest.raises(IngestionException, match="Sad face"):
        collection.build_from_file_links([file_link], raise_errors=True)

    session.set_response(BadRequest("Generic Failure", None))
    with pytest.raises(BadRequest):
        assert collection.build_from_file_links([file_link], raise_errors=False)
    session.set_response(BadRequest("path", FakeRequestResponseApiError(400, "Bad Request", [validation_error])))
    failed = collection.build_from_file_links([file_link], raise_errors=False)

    def _raise_exception():
        raise RuntimeError()

    with monkeypatch.context() as m:
        # There should be no calls given a failed ingest object
        m.setattr(Session, 'request', _raise_exception)
        assert not failed.status().success
        assert not failed.build_objects().success
        with pytest.raises(JobFailureError):
            assert not failed.build_objects_async()
        with pytest.raises(JobFailureError):
            assert not failed.poll_for_job_completion(None)
        failed.raise_errors = True
        with pytest.raises(JobFailureError):
            assert not failed.status().success

    with pytest.raises(IngestionException):
        collection.build_from_file_links([file_link], raise_errors=True)

    ingest.raise_errors = True
    session.set_responses(
        JobSubmissionResponseDataFactory(),
        JobStatusResponseDataFactory(),
        IngestionStatusResponseDataFactory(
            errors=[{
                "family": IngestionErrorFamily.DATA,
                "error_type": IngestionErrorType.MISSING_RAW_FOR_INGREDIENT,
                "level": IngestionErrorLevel.ERROR,
                "msg": "Missing ingredient: \"myristic (14:0)\" (Note ingredient IDs are case sensitive)"
            }]
        ),
    )
    with pytest.raises(IngestionException, match="Missing ingredient"):
        ingest.build_objects()
