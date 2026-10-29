"""Tests for polling job status."""

import uuid
from unittest import mock

import pytest

from citrine.exceptions import JobFailureError, PollingTimeoutError
from citrine.jobs.job import JobStatus, JobSubmissionResponse, _poll_for_job_completion
from tests.utils.factories import (
    JobStatusResponseDataFactory,
    JobSubmissionResponseDataFactory,
    TaskNodeDataFactory,
)
from tests.utils.session import FakeSession


@mock.patch("citrine.jobs.job.sleep", return_value=None)
def test_poll_failure_raises(sleep_mock):
    session = FakeSession()
    session.set_response(
        JobStatusResponseDataFactory(failure=True, tasks=[TaskNodeDataFactory(failure=True)])
    )
    job = JobSubmissionResponse.build(JobSubmissionResponseDataFactory())

    with pytest.raises(JobFailureError) as exception:
        _poll_for_job_completion(session, job, team_id=uuid.uuid4())

    assert exception.value.job_id == job.job_id
    assert len(exception.value.failure_reasons) == 1


@mock.patch("citrine.jobs.job.time", side_effect=[0.0, 0.5, 1000.0])
@mock.patch("citrine.jobs.job.sleep", return_value=None)
def test_poll_timeout_raises(sleep_mock, time_mock):
    session = FakeSession()
    pending = JobStatusResponseDataFactory(status=JobStatus.PENDING)
    session.set_responses(pending, pending)
    job = JobSubmissionResponse.build(JobSubmissionResponseDataFactory())

    with pytest.raises(PollingTimeoutError):
        _poll_for_job_completion(session, job, team_id=uuid.uuid4(), timeout=1.0)

    assert sleep_mock.call_count == 1
