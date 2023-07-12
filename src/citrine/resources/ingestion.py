from typing import Optional, Iterator, Iterable
from uuid import UUID

from citrine._rest.collection import Collection
from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine._session import Session
from citrine.exceptions import BadRequest
from citrine.jobs.job import JobSubmissionResponse, JobFailureError, _poll_for_job_completion
from citrine.resources.api_error import ValidationError
from citrine.resources.status_detail import StatusDetail, StatusLevelEnum


class IngestionStatus(Resource['IngestionStatus']):
    """
    [ALPHA] An object that represents the outcome of an ingestion event.

    Attributes
    ----------
    status: String

    errors: List[String]

    """

    status = properties.String("status")
    errors = properties.List(properties.Object(StatusDetail), "errors")

    @property
    def success(self) -> bool:
        """Whether the Ingestion operation was error-free."""
        return len(self.errors) == 0


class Ingestion(Resource['Ingestion']):
    """
    [ALPHA] A job that uploads new information to the platform.

    Datasets are the basic unit of access control. A user with read access to a dataset can view
    every object in that dataset. A user with write access to a dataset can create, update,
    and delete objects in the dataset.

    Attributes
    ----------
    uid: UUID
        Unique uuid4 identifier of this ingestion.

    """

    uid = properties.UUID('ingestion_id')
    project_id = properties.UUID('project_id')
    dataset_id = properties.UUID('dataset_id')
    session = properties.Object(Session, 'session', serializable=False)
    raise_errors = properties.Optional(properties.Boolean(), 'raise_errors', default=True)

    def build_objects(self,
                      *,
                      build_table: bool = False,
                      delete_dataset_contents: bool = False,
                      delete_templates: bool = True) -> IngestionStatus:
        """
        [ALPHA] Perform a complete ingestion operation, from start to finish.

        Initiates an ingestion operation, polls the server to determine when the job
        has finished, and returns the outcome.

        Parameters
        ----------
        build_table: bool
            Whether to build a table immediately after ingestion.  Default : False
        delete_dataset_contents: bool
            Whether to delete objects prior to generating new gemd objects.  Default: False.
        delete_templates: bool
            Whether to delete all objects and templates (as opposed to not deleting
            templates) when `delete_dataset_contents` is True.  Default: True

        Returns
        ----------
        JobSubmissionResponse
            The object for the submitted job

        """
        try:
            job = self.build_objects_async(build_table=build_table,
                                           delete_dataset_contents=delete_dataset_contents,
                                           delete_templates=delete_templates)
        except JobFailureError as e:
            if self.raise_errors:
                raise e
            else:
                return IngestionStatus.build({
                    "status": "Failure",
                    "errors": [StatusDetail(msg=err, level=StatusLevelEnum.ERROR)
                               for err in e.failure_reasons],
                })

        self.poll_for_job_completion(job)
        status = self.status()

        if self.raise_errors and not status.success:
            errors = [e.msg for e in status.errors]
            raise JobFailureError(
                message=f"Job succeeded but ingestion failed: {errors}",
                job_id=job.job_id,
                failure_reasons=errors
            )

        return status

    def build_objects_async(self,
                            *,
                            build_table: bool = False,
                            delete_dataset_contents: bool = False,
                            delete_templates: bool = True) -> JobSubmissionResponse:
        """
        [ALPHA] Begin an async ingestion operation.

        Parameters
        ----------
        build_table: bool
            Whether to build a table immediately after ingestion.  Default : False
        delete_dataset_contents: bool
            Whether to delete objects prior to generating new gemd objects.  Default: False.
        delete_templates: bool
            Whether to delete all objects and templates (as opposed to not deleting
            templates) when `delete_dataset_contents` is True.  Default: True

        Returns
        ----------
        JobSubmissionResponse
            The object for the submitted job

        """
        collection = IngestionCollection(project_id=self.project_id,
                                         dataset_id=self.dataset_id,
                                         session=self.session)
        path = collection._get_path(uid=self.uid, action="gemd-objects-async")
        params = {
            "build_table": build_table,
            "delete_dataset_contents": delete_dataset_contents,
            "delete_templates": delete_templates,
        }
        try:
            return JobSubmissionResponse.build(
                self.session.post_resource(path=path, json={}, params=params)
            )
        except BadRequest as e:
            if e.api_error is not None:
                errors = [err.failure_message for err in e.api_error.validation_errors]
                if len(errors) == 0:
                    errors = [e.api_error.message]

                raise JobFailureError(
                    message=e.api_error.message,
                    job_id=None,
                    failure_reasons=errors
                )
            else:
                raise e

    def poll_for_job_completion(self,
                                job: JobSubmissionResponse,
                                *,
                                timeout: Optional[float] = None,
                                polling_delay: Optional[float] = None
                                ) -> IngestionStatus:
        """
        [ALPHA] Repeatedly ask server if a job associated with this ingestion has completed.

        Parameters
        ----------
        job: JobSubmissionResponse
            The job to check on
        timeout
            Amount of time to wait on the job (in seconds) before giving up. Note that
            this number has no effect on the underlying job itself, which can also time
            out server-side.
        polling_delay:
            How long to delay between each polling retry attempt.

        Returns
        ----------
        IngestionStatus
            A string representation of the status


        """
        kwargs = {}
        if timeout is not None:
            kwargs["timeout"] = timeout
        if polling_delay is not None:
            kwargs["polling_delay"] = polling_delay

        _poll_for_job_completion(
            session=self.session,
            project_id=self.project_id,
            job=job,
            raise_errors=False,  # JobFailureError doesn't contain the error
            **kwargs
        )
        return self.status()

    def status(self) -> IngestionStatus:
        """
        [ALPHA] Retrieve the status of the ingestion  from platform.

        Returns
        ----------
        IngestionStatus
            The result of the ingestion attempt

        """
        collection = IngestionCollection(project_id=self.project_id,
                                         dataset_id=self.dataset_id,
                                         session=self.session)
        path = collection._get_path(uid=self.uid, action="status")
        return IngestionStatus.build(self.session.get_resource(path=path))


class FailedIngestion(Ingestion):
    """[ALPHA] Object to fill in when building an ingest fails."""

    def __init__(self, errors: Iterable[ValidationError]):
        self.errors = [StatusDetail(msg=err.failure_message, level=StatusLevelEnum.ERROR)
                       for err in errors]
        self.raise_errors = False

    def build_objects(self,
                      *,
                      build_table: bool = False,
                      delete_dataset_contents: bool = False,
                      delete_templates: bool = True) -> IngestionStatus:
        """[ALPHA] Satisfy the required interface for a failed ingestion."""
        return self.status()

    def build_objects_async(self,
                            *,
                            build_table: bool = False,
                            delete_dataset_contents: bool = False,
                            delete_templates: bool = True) -> JobSubmissionResponse:
        """[ALPHA] Satisfy the required interface for a failed ingestion."""
        raise JobFailureError(
            message=f"Errors: {[e.msg for e in self.errors]}",
            job_id=None,
            failure_reasons=[e.msg for e in self.errors]
        )

    def poll_for_job_completion(self,
                                job: JobSubmissionResponse,
                                *,
                                timeout: Optional[float] = None,
                                polling_delay: Optional[float] = None
                                ) -> IngestionStatus:
        """[ALPHA] Satisfy the required interface for a failed ingestion."""
        raise JobFailureError(
            message=f"Errors: {[e.msg for e in self.errors]}",
            job_id=None,
            failure_reasons=[e.msg for e in self.errors]
        )

    def status(self) -> IngestionStatus:
        """
        [ALPHA] Retrieve the status of the ingestion  from platform.

        Returns
        ----------
        IngestionStatus
            The result of the ingestion attempt

        """
        if self.raise_errors:
            raise JobFailureError(
                message=f"Ingestion creation failed: self.errors",
                job_id=None,
                failure_reasons=self.errors
            )
        else:
            return IngestionStatus.build({
                "status": "Failure",
                "errors": self.errors,
            })


class IngestionCollection(Collection[Ingestion]):
    """
    [ALPHA] Represents the collection of all ingestion operations.

    Parameters
    ----------
    project_id: UUID
        Unique ID of the project this dataset collection belongs to.
    session: Session
        The Citrine session used to connect to the database.

    """

    _path_template = 'projects/{project_id}/ingestions'
    _individual_key = None
    _collection_key = None
    _resource = Ingestion

    def __init__(self, project_id: UUID, dataset_id: UUID, session: Session):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.session = session

    def build_from_file_links(self,
                              file_links: Iterable["FileLink"],
                              *,
                              raise_errors: bool = True) -> Ingestion:
        """
        [ALPHA] Create an on-platform ingestion event based on the passed FileLink objects.

        Parameters
        ----------
        file_links: Iterable[FileLink]
            The files to ingest.
        raise_errors: bool
            Whether ingestion errors raise exceptions (vs. simply reported in the results).
            Default: True

        """
        if len(file_links) == 0:
            raise ValueError(f"No files passed.")
        invalid_links = [f for f in file_links if f.uid is None]
        if len(invalid_links) != 0:
            raise ValueError(f"{len(invalid_links)} File Links have no on-platform UID.")

        req = {
            "dataset_id": str(self.dataset_id),
            "project_id": str(self.project_id),
            "files": [
                {"dataset_file_id": str(f.uid), "file_version_uuid": str(f.version)}
                for f in file_links
            ]
        }

        try:
            response = self.session.post_resource(path=self._get_path(), json=req)
        except BadRequest as e:
            if e.api_error is not None:
                errors = e.api_error.validation_errors
                if len(errors) == 0:
                    errors = [ValidationError.build({"failure_message": e.api_error.message,
                                                     "failure_id": "failure_id"})
                              ]
                if raise_errors:
                    raise JobFailureError(
                        message=e.api_error.message,
                        job_id=None,
                        failure_reasons=errors
                    )
                else:
                    return FailedIngestion(errors=errors)
            else:
                raise e
        return self.build({
            **response,
            "raise_errors": raise_errors
        })

    def build(self, data: dict) -> Ingestion:
        """Build an instance of an Ingestion."""
        result = Ingestion.build({**data, "session": self.session})
        return result

    def register(self, model: Ingestion) -> Ingestion:
        """Cannot register an Ingestion."""
        raise NotImplementedError("Cannot register an Ingestion.")

    def update(self, model: Ingestion) -> Ingestion:
        """Cannot update an Ingestion."""
        raise NotImplementedError("Cannot update an Ingestion.")

    def delete(self, model: Ingestion) -> Ingestion:
        """Cannot delete an Ingestion."""
        raise NotImplementedError("Cannot delete an Ingestion.")

    def list(self, *, per_page: int = 100) -> Iterator[Ingestion]:
        """Cannot list Ingestions."""
        raise NotImplementedError("Cannot list Ingestions.")
