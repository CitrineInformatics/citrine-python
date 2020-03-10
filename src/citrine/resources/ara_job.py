from typing import List, Union, Optional, Set
from uuid import UUID
from uuid import uuid4

from citrine._serialization.properties import Set as PropertySet, String, Property, Object
from citrine._rest.resource import Resource
from citrine._session import Session
from citrine.resources.api_error import ApiError
from citrine.resources.ara_definition import AraDefinition
from citrine.resources.project import Project
from citrine._serialization import properties


class JobSubmissionResponse(Resource['AraJobStatus']):
    """
    [ALPHA] a response to a submit-job request for the job submission framework

    Parameters
    ----------
    job_id: UUID
        job id of the of a job submission request
    """
    job_id = properties.UUID("job_id")

    def __init__(self, job_id: UUID):
        self.job_id = job_id


class TaskNode(Resource['TaskNode']):
    """
    [ALPHA] individual task status

    Parameters
    ----------
    id: str
        unique identification number for the job task.
    task_type: str
        the type of task running
    status: str
        the last reported status of this particular task.
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
    """
    [ALPHA] a response to a job status check

    Parameters
    ----------
    job_type: str
        the type of job for this status report
    status: str
        the actual status of the job
    tasks: List[TaskNode]
        all of the constituent task required to complete this job
    """

    job_type = properties.String("job_type")
    status = properties.String("status")
    tasks = properties.List(Object(TaskNode), "tasks")

    def __init__(
            self,
            job_type: str,
            status: str,
            tasks: List[TaskNode]
    ):
        self.job_type = job_type
        self.status = status
        self.tasks = tasks


class AraJobFramework(Resource["AraJobFramework"]):
    """
    [ALPHA] a resource for submitting a job and getting job status

    Parameters
    ----------
    session: Session
        the remote session for hitting framework endpoints
    """
    _path_template = 'projects/{project_id}'

    def __init__(self, session: Session):
        self.session = session

    def build_ara_table(self, project: Project,
                        ara_def: AraDefinition) -> Union[ApiError, JobSubmissionResponse]:
        """
        [ALPHA] submit an ara table construction job

        This method makes a call out to the job framework to start a new job to build
        the respective table for a given AraDefinition.

        Parameters
        ----------
        project: Project
            The project on behalf of which the job executes.
        ara_def: AraDefinition
            the ara definition describing the new table
        """
        job_id = uuid4()
        url_suffix: str = "/ara-definitions/{ara_definition}/versions/{version_number}/build?job_id={job_id}"
        path: str = self._path_template.format(
            project_id=project.uid
        ) + url_suffix.format(
            ara_definition=ara_def.definition_uid,
            version_number=ara_def.version_number,
            job_id=job_id
        )
        response: dict = self.session.post_resource(path=path, json={})
        return JobSubmissionResponse.build(response)

    def get_job_status(self, project: Project, job_id: str):
        """
        [ALPHA] get status of a running job

        Parameters
        ----------
        project: Project
            The project on behalf of which we retrieve a job status
        job_id: str
            The job we retrieve the status for
        """
        url_suffix: str = "/execution/job-status?job_id={job_id}"
        path: str = self._path_template.format(
            project_id=project.uid
        ) + url_suffix.format(job_id=job_id)
        response: dict = self.session.get_resource(path=path)
        return JobStatusResponse.build(response)
