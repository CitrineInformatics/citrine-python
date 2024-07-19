from logging import getLogger
from time import time, sleep
from typing import Union
from uuid import UUID

from citrine._rest.resource import Resource
from citrine._serialization.properties import Set as PropertySet, String, Object
from citrine._serialization import properties
from citrine._session import Session
from citrine._utils.functions import format_escaped_url
from citrine.exceptions import PollingTimeoutError, JobFailureError

logger = getLogger(__name__)


class JobSubmissionResponse(Resource['JobSubmissionResponse']):
    """A response to a submit-job request for the job submission framework.

    This is returned as a successful response from the remote service.
    """

    job_id = properties.UUID("job_id")
    """:UUID: job id of the job submission request"""


class TaskNode(Resource['TaskNode']):
    """Individual task status.

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


class JobStatusResponse(Resource['JobStatusResponse']):
    """A response to a job status check.

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


def _poll_for_job_completion(session: Session,
                             job: Union[JobSubmissionResponse, UUID, str],
                             *,
                             team_id: Union[UUID, str],
                             timeout: float = 2 * 60,
                             polling_delay: float = 2.0,
                             raise_errors: bool = True,
                             ) -> JobStatusResponse:
    """
    Polls for job completion given a timeout.

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
    raise_errors:
        Whether a `Failure` response should raise a JobFailureError.

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
    path = format_escaped_url('teams/{}/execution/job-status', team_id)
    params = {'job_id': job_id}
    start_time = time()
    while True:
        response = session.get_resource(path=path, params=params)
        status: JobStatusResponse = JobStatusResponse.build(response)
        if status.status in ['Success', 'Failure']:
            break
        elif time() - start_time < timeout:
            logger.info(
                f'Job still in progress, polling status again in {polling_delay:.2f} seconds.'
            )

            sleep(polling_delay)
        else:
            logger.error(f'Job exceeded user timeout of {timeout} seconds. '
                         f'Note job on server is unaffected by this timeout.')
            logger.debug('Last status: {}'.format(status.dump()))
            raise PollingTimeoutError('Job {} timed out.'.format(job_id))
    if status.status == 'Failure':
        logger.debug(f'Job terminated with Failure status: {status.dump()}')
        if raise_errors:
            failure_reasons = []
            for task in status.tasks:
                if task.status == 'Failure':
                    logger.error(f'Task {task.id} failed with reason "{task.failure_reason}"')
                    failure_reasons.append(task.failure_reason)
            raise JobFailureError(
                message=f'Job {job_id} terminated with Failure status. '
                        f'Failure reasons: {failure_reasons}',
                job_id=job_id,
                failure_reasons=failure_reasons)

    return status
