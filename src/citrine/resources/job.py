from typing import List, Optional, Set, Dict
from uuid import UUID

from citrine._serialization.properties import Set as PropertySet, String, Object
from citrine._rest.resource import Resource
from citrine._serialization import properties


class JobSubmissionResponse(Resource['AraJobStatus']):
    """[ALPHA] a response to a submit-job request for the job submission framework.

    This is returned as a successful response from the remote service.

    Parameters
    ----------
    job_id: UUID
        job id of the of a job submission request

    """

    job_id = properties.UUID("job_id")

    def __init__(self, job_id: UUID):
        self.job_id = job_id


class TaskNode(Resource['TaskNode']):
    """[ALPHA] individual task status.

    The TaskNode describes a component of an overall job.

    Parameters
    ----------
    id: str
        unique identification number for the job task.
    task_type: str
        the type of task running
    status: str
        the last reported status of this particular task.
        One of "Submitted", "Pending", "Running", "Success", or "Failure".
    dependencies: Set[str]
        all the tasks that this task is dependent on.
    failure_reason: Optional[str]
        if a task has failed, the failure reason will be in this parameter.

    """

    id = properties.String("id")
    task_type = properties.String("task_type")
    status = properties.String("status")
    dependencies = PropertySet(String(), "dependencies")
    failure_reason = properties.Optional(String(), "failure_reason")

    def __init__(
            self,
            id: str,
            task_type: str,
            status: str,
            dependencies: Set[str],
            failure_reason: Optional[str]
    ):
        self.id = id
        self.task_type = task_type
        self.status = status
        self.dependencies = dependencies
        self.failure_reason = failure_reason


class JobStatusResponse(Resource['JobStatusResponse']):
    """[ALPHA] a response to a job status check.

    The JobStatusResponse summarizes the status for the entire job.

    Parameters
    ----------
    job_type: str
        the type of job for this status report
    status: str
        the actual status of the job.
        One of "Running", "Success", or "Failure".
    tasks: List[TaskNode]
        all of the constituent task required to complete this job
    output: Optional[Map[String,String]]
        job output properties and results

    """

    job_type = properties.String("job_type")
    status = properties.String("status")
    tasks = properties.List(Object(TaskNode), "tasks")
    output = properties.Optional(properties.Mapping(String, String), 'output')

    def __init__(
            self,
            job_type: str,
            status: str,
            tasks: List[TaskNode],
            output: Optional[Dict[str, str]]
    ):
        self.job_type = job_type
        self.status = status
        self.tasks = tasks
        self.output = output
