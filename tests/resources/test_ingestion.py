import pytest
from uuid import uuid4

from citrine._session import Session
from citrine.exceptions import BadRequest
from citrine.resources.api_error import ValidationError
from citrine.resources.dataset import Dataset
from citrine.resources.file_link import FileLink
from citrine.resources.ingestion import Ingestion, IngestionStatus, IngestionCollection
from citrine.jobs.job import JobSubmissionResponse, JobStatusResponse, JobFailureError

from tests.utils.factories import DatasetFactory
from tests.utils.session import FakeSession, FakeRequestResponseApiError


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def dataset(session: Session):
    dataset = DatasetFactory(name='Test Dataset')
    dataset.project_id = uuid4()
    dataset.uid = uuid4()
    dataset.session = session

    return dataset


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
        "project_id": collection.project_id,
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
        "status": "Green",
        "errors": []
    })


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


def test_poll_for_job_completion_signature(ingest, operation, status, monkeypatch):
    """Test calls on polling."""

    outer_timeout = None
    outer_polling_delay = None
    outer_raise_errors = None

    def _mock_poll_for_job_completion(
            session,
            project_id,
            job,
            *,
            timeout=-1.0,
            polling_delay=-2.0,
            raise_errors=True):
        nonlocal outer_timeout
        nonlocal outer_polling_delay
        nonlocal outer_raise_errors
        outer_timeout = timeout
        outer_polling_delay = polling_delay
        outer_raise_errors = raise_errors

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

    def _mock_poll_for_job_completion(self, job, **_):
        response = {
            "job_type": "Ingestion!!!!! :D",
            "status": "Success",
            "tasks": [],
            "output": dict()
        }
        return JobStatusResponse.build(response)

    # This is mocked equivalently for all tests
    monkeypatch.setattr(Ingestion, "poll_for_job_completion", _mock_poll_for_job_completion)
    validation_error = ValidationError.build({"failure_message": "you failed", "failure_id": "failure_id"})

    # Raise exceptions, but it worked
    ingest.raise_errors = True
    session.set_responses(
        {"job_id": str(uuid4())},
        {"status": "Green", "errors": []}
    )
    result = ingest.build_objects()
    assert result.success
    assert len(result.errors) == 0

    # Raise exceptions, and build_objects_async returned errors
    ingest.raise_errors = True
    session.set_responses(
        BadRequest("path", FakeRequestResponseApiError(400, "Bad Request", [validation_error])),
        {"status": "Green", "errors": []}
    )
    with pytest.raises(JobFailureError, match="Bad Request"):
        ingest.build_objects()

    # Raise exceptions, and build_objects_async returned unspecified errors
    ingest.raise_errors = True
    session.set_responses(
        BadRequest("path", FakeRequestResponseApiError(400, "This has no details", [])),
        {"status": "Green", "errors": []}
    )
    with pytest.raises(JobFailureError, match="no details"):
        ingest.build_objects()

    # Raise exceptions, and build_objects_async had server errors
    ingest.raise_errors = True
    session.set_responses(
        BadRequest("path", FakeRequestResponseApiError(500, "This was internal", [])),
        {"status": "Green", "errors": []}
    )
    with pytest.raises(JobFailureError, match="internal"):
        ingest.build_objects()

    # Raise exceptions, and status returned errors
    ingest.raise_errors = True
    session.set_responses(
        {"job_id": str(uuid4())},
        {"status": "Red", "errors": [{"msg": "Bad things!", "level": "error"}]}
    )
    with pytest.raises(JobFailureError, match="Bad things"):
        ingest.build_objects()

    # Suppress exceptions, but it worked
    ingest.raise_errors = False
    session.set_responses(
        {"job_id": str(uuid4())},
        {"status": "Green", "errors": []}
    )
    result = ingest.build_objects()
    assert result.success

    # Suppress exceptions, and build_objects_async returned errors
    ingest.raise_errors = False
    session.set_responses(
        BadRequest("path", FakeRequestResponseApiError(400, "Bad Request", [validation_error])),
        {"status": "Green", "errors": [{"msg": validation_error.failure_message, "level": "error"}]}
    )
    result = ingest.build_objects()
    assert not result.success
    assert any('you failed' in e.msg for e in result.errors)

    # Suppress exceptions, and build_objects_async returned errors
    ingest.raise_errors = False
    session.set_responses(
        BadRequest("No API error, so it's thrown", None),
        {"status": "Green", "errors": [{"msg": validation_error.failure_message, "level": "error"}]}
    )
    with pytest.raises(BadRequest):
        ingest.build_objects()

    # Suppress exceptions, and status returned errors
    ingest.raise_errors = False
    session.set_responses(
        {"job_id": str(uuid4())},
        {"status": "Red", "errors": [{"msg": "Sad", "level": "error"}] * 3}
    )
    result = ingest.build_objects()
    assert not result.success
    assert any('Sad' in e.msg for e in result.errors)


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
    with pytest.raises(JobFailureError, match="Sad face"):
        assert collection.build_from_file_links([file_link], raise_errors=True)

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

    with pytest.raises(JobFailureError):
        collection.build_from_file_links([file_link], raise_errors=True)

    ingest.raise_errors = True
    session.set_responses(
        {"job_id": uuid4()},
        {"job_type": "Ingestion!!!!! :D", "status": "Success", "tasks": [], "output": dict()},
        {
            "ingestion_id": ingest.uid,
            "status": "ingestion_created",
            "errors": [{
                "family": "data",
                "error_type": "missing_raw_for_ingredient",
                "level": "error",
                "msg": "Missing ingredient: \"myristic (14:0)\" (Note ingredient IDs are case sensitive)"
            }]
        }
    )
    with pytest.raises(JobFailureError, match="Missing ingredient"):
        ingest.build_objects()
