import citrine.jobs.job
from citrine.jobs.job import _poll_for_job_completion  # noqa
from citrine._utils.functions import MigratedClassMeta


class JobSubmissionResponse(citrine.jobs.job.JobSubmissionResponse,
                            deprecated_in="2.22.1",
                            removed_in="3.0.0",
                            metaclass=MigratedClassMeta):
    """
    A response to a submit-job request for the job submission framework.

    This is returned as a successful response from the remote service.

    Importing from this package is deprecated; import from citrine.jobs.job instead.

    """


class TaskNode(citrine.jobs.job.TaskNode,
               deprecated_in="2.22.1",
               removed_in="3.0.0",
               metaclass=MigratedClassMeta):
    """
    Individual task status.

    The TaskNode describes a component of an overall job.

    Importing from this package is deprecated; import from citrine.jobs.job instead.

    """


class JobStatusResponse(citrine.jobs.job.JobStatusResponse,
                        deprecated_in="2.22.1",
                        removed_in="3.0.0",
                        metaclass=MigratedClassMeta):
    """
    A response to a job status check.

    The JobStatusResponse summarizes the status for the entire job.

    Importing from this package is deprecated; import from citrine.jobs.job instead.

    """
