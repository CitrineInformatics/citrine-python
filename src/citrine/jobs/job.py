from logging import getLogger
from typing import Union
from uuid import UUID

from time import time, sleep

from citrine._serialization.properties import Set as PropertySet, String, Object
from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine._session import Session
from citrine._utils.functions import format_escaped_url
from citrine.exceptions import PollingTimeoutError, JobFailureError

logger = getLogger(__name__)


class JobSubmissionResponse(Resource['AraJobStatus']):
    """[ALPHA] a response to a submit-job request for the job submission framework.

    This is returned as a successful response from the remote service.
    """

    job_id = properties.UUID("job_id")
    """:UUID: job id of the job submission request"""

    def __init__(self):
        pass  # pragma: no cover


class TaskNode(Resource['TaskNode']):
    """[ALPHA] individual task status.

    The TaskNode describes a component of an overall job.
    """

    id = properties.String("id")
    """:str: unique identification number for the job task"""
    task_type = properties.String("task_type")
    """:str: the type of task running"""
    status = properties.String("status")
    """:str: The last reported status of this particular task.
    One of "Submitted", "Pending", "Running", "Success", or "Failure"."""
    dependencies = PropertySet(String(), "dependencies")
    """:Set[str]: all the tasks that this task is dependent on"""
    failure_reason = properties.Optional(String(), "failure_reason")
    """:str: if a task has failed, the failure reason will be in this parameter"""

    def __init__(self):
        pass  # pragma: no cover


class JobStatusResponse(Resource['JobStatusResponse']):
    """[ALPHA] a response to a job status check.

    The JobStatusResponse summarizes the status for the entire job.
    """

    job_type = properties.String("job_type")
    """:str: the type of job for this status report"""
    status = properties.String("status")
    """:str: The status of the job. One of "Running", "Success", or "Failure"."""
    tasks = properties.List(Object(TaskNode), "tasks")
    """:List[TaskNode]: all of the constituent task required to complete this job"""
    output = properties.Optional(properties.Mapping(String, String), 'output')
    """:Optional[dict[str, str]]: job output properties and results"""

    def __init__(self):
        pass  # pragma: no cover


def _poll_for_job_completion(session: Session, project_id: Union[UUID, str],
                             job: Union[JobSubmissionResponse, UUID, str], *,
                             timeout: float = 2 * 60,
                             polling_delay: float = 2.0) -> JobStatusResponse:
    """
    Polls for job completion given a timeout, failing with an exception on job failure.

    This polls for job completion given the Job ID, failing appropriately if the job result
    was not successful.

    Parameters
    ----------
    job
        The job submission object or job ID that was given from a job submission.
    timeout
        Amount of time to wait on the job (in seconds) before giving up. Defaults
        to 2 minutes. Note that this number has no effect on the underlying job
        itself, which can also time out server-side.
    polling_delay:
        How long to delay between each polling retry attempt.

    Returns
    -------
    JobStatusResponse
        The job response information that can be used to extract relevant
        information from the completed job.

    """
    if isinstance(job, JobSubmissionResponse):
        job_id = job.job_id
    else:
        job_id = job  # pragma: no cover
    path = format_escaped_url('projects/{}/execution/job-status', project_id)
    params = {'job_id': job_id}
    start_time = time()
    while True:
        response = session.get_resource(path=path, params=params)
        status: JobStatusResponse = JobStatusResponse.build(response)
        if status.status in ['Success', 'Failure']:
            break
        elif time() - start_time < timeout:
            logger.info('Job still in progress, polling status again in {:.2f} seconds.'
                        .format(polling_delay))

            sleep(polling_delay)
        else:
            logger.error('Job exceeded user timeout of {} seconds.'.format(timeout))
            logger.debug('Last status: {}'.format(status.dump()))
            raise PollingTimeoutError('Job {} timed out.'.format(job_id))
    if status.status == 'Failure':
        logger.debug('Job terminated with Failure status: {}'.format(status.dump()))
        failure_reasons = []
        for task in status.tasks:
            if task.status == 'Failure':
                logger.error('Task {} failed with reason "{}"'.format(
                    task.id, task.failure_reason))
                failure_reasons.append(task.failure_reason)
        raise JobFailureError(
            message='Job {} terminated with Failure status. Failure reasons: {}'.format(
                job_id, failure_reasons), job_id=job_id,
            failure_reasons=failure_reasons)

    return status
