import pytest
from uuid import uuid4

from citrine.resources.file_link import FileLink
from citrine.resources.ingestion import Ingestion, IngestionStatus, IngestionCollection
from citrine.jobs.job import JobSubmissionResponse, JobStatusResponse, JobFailureError

from tests.utils.session import FakeSession


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def collection(session) -> IngestionCollection:
    return IngestionCollection(
        project_id=uuid4(),
        dataset_id=uuid4(),
        session=session
    )


@pytest.fixture
def ingest(collection) -> Ingestion:
    return collection.build({
        "project_id": collection.project_id,
        "dataset_id": collection.dataset_id
    })


@pytest.fixture
def operation() -> JobSubmissionResponse:
    return JobSubmissionResponse.build({
        "job_id": uuid4()
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


def test_poll_for_job_completion_signature(ingest, operation, monkeypatch):
    """Test calls on polling."""

    outer_timeout = None
    outer_polling_delay = None

    def _mock_poll_for_job_completion(session, project_id, job, *, timeout=-1.0, polling_delay=-2.0):
        nonlocal outer_timeout
        nonlocal outer_polling_delay
        outer_timeout = timeout
        outer_polling_delay = polling_delay

    monkeypatch.setattr("citrine.resources.ingestion._poll_for_job_completion", _mock_poll_for_job_completion)

    ingest.poll_for_job_completion(operation)
    assert outer_timeout == -1.0
    assert outer_polling_delay == -2.0

    ingest.poll_for_job_completion(operation, timeout=20.0, polling_delay=5.0)
    assert outer_timeout == 20.0
    assert outer_polling_delay == 5.0


def test_processing_exceptions(ingest, monkeypatch):

    def _mock_build_objects_async(self, **_):
        return JobSubmissionResponse.build({"job_id": uuid4()})

    def _mock_poll_for_job_completion_fail(self, job, **_):
        failure_reasons = ['Cuz I said so']
        raise JobFailureError(message=f'Ingestion ID: {self.uid}, {failure_reasons}',
                              job_id=job.job_id,
                              failure_reasons=failure_reasons)

    def _mock_poll_for_job_completion_success(self, job, **_):
        response = {
            "job_type": "Ingestion!!!!! :D",
            "status": "Success",
            "tasks": [],
            "output": dict()
        }
        return JobStatusResponse.build(response)

    def _mock_status_fail(self):
        response = {
            "status": "created",
            "errors": ["It wasn't everything you hoped for"]
        }
        return IngestionStatus.build(response)

    def _mock_status_success(self):
        response = {
            "status": "created",
            "errors": []
        }
        return IngestionStatus.build(response)

    # This is mocked equivalently for all tests
    monkeypatch.setattr(Ingestion, "build_objects_async", _mock_build_objects_async)

    with monkeypatch.context() as m:  # Raise exceptions, but it worked
        m.setattr(Ingestion, "poll_for_job_completion", _mock_poll_for_job_completion_success)
        m.setattr(Ingestion, "status", _mock_status_success)

        result = ingest.build_objects(raise_errors=True)
        assert result.success
        assert len(result.errors) == 0

    with monkeypatch.context() as m:  # Raise exceptions, and failed during polling
        m.setattr(Ingestion, "poll_for_job_completion", _mock_poll_for_job_completion_fail)
        m.setattr(Ingestion, "status", _mock_status_success)

        with pytest.raises(JobFailureError, match='Cuz I said so'):
            ingest.build_objects(raise_errors=True)

    with monkeypatch.context() as m:  # Raise exceptions, and returned errors
        m.setattr(Ingestion, "poll_for_job_completion", _mock_poll_for_job_completion_success)
        m.setattr(Ingestion, "status", _mock_status_fail)

        with pytest.raises(JobFailureError, match="It wasn't everything you hoped for"):
            ingest.build_objects(raise_errors=True)

    with monkeypatch.context() as m:  # Suppress exceptions, but it worked
        m.setattr(Ingestion, "poll_for_job_completion", _mock_poll_for_job_completion_success)
        m.setattr(Ingestion, "status", _mock_status_success)

        result = ingest.build_objects(raise_errors=False)
        assert result.success

    with monkeypatch.context() as m:  # Suppress exceptions, and failed during polling
        m.setattr(Ingestion, "poll_for_job_completion", _mock_poll_for_job_completion_fail)
        m.setattr(Ingestion, "status", _mock_status_success)

        result = ingest.build_objects(raise_errors=False)
        assert not result.success
        assert any('Cuz I said so' in e for e in result.errors)

    with monkeypatch.context() as m:  # Suppress exceptions, and returned errors
        m.setattr(Ingestion, "poll_for_job_completion", _mock_poll_for_job_completion_success)
        m.setattr(Ingestion, "status", _mock_status_fail)

        result = ingest.build_objects(raise_errors=False)
        assert not result.success
        assert any('everything' in e for e in result.errors)


def test_ingestion_flow(collection: IngestionCollection):
    with pytest.raises(ValueError, match="UID"):
        collection.build_from_file_links([FileLink(filename="mine.txt", url="http:/external.com")])
