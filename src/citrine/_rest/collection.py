import warnings
from abc import abstractmethod
from logging import getLogger
from typing import Optional, Union, Generic, TypeVar, Iterable
from uuid import UUID

from time import time, sleep

from citrine._rest.paginator import Paginator
from citrine._rest.pageable import Pageable
from citrine.exceptions import ModuleRegistrationFailedException, NonRetryableException, \
    PollingTimeoutError, JobFailureError
from citrine.informatics.modules import ModuleRef
from citrine.resources.job import JobSubmissionResponse, JobStatusResponse
from citrine.resources.response import Response

logger = getLogger(__name__)

ResourceType = TypeVar('ResourceType', bound='Resource')

# Python does not support a TypeVar being used as a bound for another TypeVar.
# Thus, this will never be particularly type safe on its own. The solution is to
# have subclasses override the create method.
CreationType = TypeVar('CreationType', bound='Resource')


class Collection(Generic[ResourceType], Pageable):
    """Abstract class for representing collections of REST resources."""

    _path_template: str = NotImplemented
    _dataset_agnostic_path_template: str = NotImplemented
    _individual_key: str = NotImplemented
    _resource: ResourceType = NotImplemented
    _collection_key: str = 'entries'
    _paginator: Paginator = Paginator()

    def _put_module_ref(self, subpath: str, workflow_id: UUID):
        url = self._get_path(subpath)
        ref = ModuleRef(str(workflow_id))
        return self.session.put_resource(url, ref.dump())

    def _get_path(self, uid: Optional[Union[UUID, str]] = None,
                  ignore_dataset: Optional[bool] = False) -> str:
        """Construct a url from __base_path__ and, optionally, id."""
        subpath = '/{}'.format(uid) if uid else ''
        if ignore_dataset:
            return self._dataset_agnostic_path_template.format(**self.__dict__) + subpath
        else:
            return self._path_template.format(**self.__dict__) + subpath

    @abstractmethod
    def build(self, data: dict):
        """Build an individual element of the collection."""

    def get(self, uid: Union[UUID, str]) -> ResourceType:
        """Get a particular element of the collection."""
        if uid is None:
            raise ValueError("Cannot get when uid=None.  Are you using a registered resource?")
        path = self._get_path(uid)
        data = self.session.get_resource(path)
        data = data[self._individual_key] if self._individual_key else data
        return self.build(data)

    def register(self, model: CreationType) -> CreationType:
        """Create a new element of the collection by registering an existing resource."""
        path = self._get_path()
        try:
            data = self.session.post_resource(path, model.dump())
            data = data[self._individual_key] if self._individual_key else data
            self._check_experimental(data)
            return self.build(data)
        except NonRetryableException as e:
            raise ModuleRegistrationFailedException(model.__class__.__name__, e)

    def list(self,
             page: Optional[int] = None,
             per_page: int = 100) -> Iterable[ResourceType]:
        """
        Paginate over the elements of the collection.

        Leaving page and per_page as default values will yield all elements in the
        collection, paginating over all available pages.

        Parameters
        ---------
        page: int, optional
            The "page" of results to list. Default is to read all pages and yield
            all results.  This option is deprecated.
        per_page: int, optional
            Max number of results to return per page. Default is 100.  This parameter
            is used when making requests to the backend service.  If the page parameter
            is specified it limits the maximum number of elements in the response.

        Returns
        -------
        Iterable[ResourceType]
            Resources in this collection.

        """
        return self._paginator.paginate(page_fetcher=self._fetch_page,
                                        collection_builder=self._build_collection_elements,
                                        page=page,
                                        per_page=per_page)

    def update(self, model: CreationType) -> CreationType:
        """Update a particular element of the collection."""
        url = self._get_path(model.uid)
        updated = self.session.put_resource(url, model.dump())
        data = updated[self._individual_key] if self._individual_key else updated
        self._check_experimental(data)
        return self.build(data)

    def delete(self, uid: Union[UUID, str]) -> Response:
        """Delete a particular element of the collection."""
        url = self._get_path(uid)
        data = self.session.delete_resource(url)
        return Response(body=data)

    def _build_collection_elements(self,
                                   collection: Iterable[dict]) -> Iterable[ResourceType]:
        """
        For each element in the collection, build the appropriate resource type.

        Parameters
        ---------
        collection: Iterable[dict]
            collection containing the elements to be built

        Returns
        -------
        Iterable[ResourceType]
            Resources in this collection.

        """
        for element in collection:
            yield self.build(element)

    def _check_experimental(self, data):
        if data.get("experimental", False):
            uid = data.get("id")
            typ = str(self._resource)
            msg = "The {} with id {} is experimental because: \n  {}".format(
                typ, uid,
                "\n  ".join(data.get("experimental_reasons") or ["Unknown reason"])
            )
            warnings.warn(msg)

    def _poll_for_job_completion(self, project_id: Union[UUID, str],
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
        path = 'projects/{}/execution/job-status'.format(project_id)
        params = {'job_id': job_id}
        start_time = time()
        while True:
            response = self.session.get_resource(path=path, params=params)
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
