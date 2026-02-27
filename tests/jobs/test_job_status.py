from citrine.jobs.job import JobStatus, JobStatusResponse, TaskNode
import pytest

from tests.utils.factories import TaskNodeDataFactory, JobStatusResponseDataFactory

def test_status_response_status():
    status_response = JobStatusResponse.build(JobStatusResponseDataFactory(failure=True))
    assert status_response.status == JobStatus.FAILURE

    with pytest.raises(ValueError):
        status_response.status = 'Failed'
    assert isinstance(status_response.status, JobStatus)

    with pytest.raises(ValueError):
        status_response.status = JobStatus.PENDING
    assert status_response.status != JobStatus.PENDING

    status_response.status = JobStatus.SUCCESS
    assert status_response.status == JobStatus.SUCCESS

def test_task_node_status():
    status_response = TaskNode.build(TaskNodeDataFactory(failure=True))
    assert status_response.status == JobStatus.FAILURE

    with pytest.raises(ValueError):
        status_response.status = 'Failed'
    assert isinstance(status_response.status, JobStatus)

    status_response.status = JobStatus.SUCCESS
    assert status_response.status == JobStatus.SUCCESS
