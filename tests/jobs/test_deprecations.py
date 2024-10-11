from citrine.jobs.job import JobStatus, JobStatusResponse, TaskNode
import pytest
import warnings

from tests.utils.factories import TaskNodeDataFactory, JobStatusResponseDataFactory

def test_status_response_status():
    status_response = JobStatusResponse.build(JobStatusResponseDataFactory(failure=True))
    assert status_response.status == JobStatus.FAILURE

    with pytest.deprecated_call():
        status_response.status = 'Failed'
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert not isinstance(status_response.status, JobStatus)

    with pytest.deprecated_call():
        status_response.status = JobStatus.PENDING
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert status_response.status == JobStatus.PENDING

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        status_response.status = JobStatus.SUCCESS
    assert status_response.status == JobStatus.SUCCESS

def test_task_node_status():
    status_response = TaskNode.build(TaskNodeDataFactory(failure=True))
    assert status_response.status == JobStatus.FAILURE

    with pytest.deprecated_call():
        status_response.status = 'Failed'
    assert not isinstance(status_response.status, JobStatus)

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        status_response.status = JobStatus.SUCCESS
        assert status_response.status == JobStatus.SUCCESS
