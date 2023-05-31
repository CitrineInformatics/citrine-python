from typing import Optional, Iterator, Iterable
from uuid import UUID

from citrine._rest.collection import Collection
from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine._session import Session
from citrine.jobs.job import JobSubmissionResponse, JobStatusResponse, JobFailureError, \
    _poll_for_job_completion


class IngestionStatus(Resource['IngestionStatus']):
    """
    [ALPHA] An object that represents the outcome of an ingestion event.

    Attributes
    ----------
    status: String

    errors: List[String]

    """

    status = properties.String("status")
    errors = properties.List(properties.String, "errors")

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

    uid = properties.Optional(properties.UUID(), 'ingestion_id')
    project_id = properties.Optional(properties.UUID(), 'project_id')
    dataset_id = properties.Optional(properties.UUID(), 'dataset_id')
    session = properties.Optional(properties.Object(Session), 'session', serializable=False)

    def build_objects(self,
                      *,
                      raise_errors: bool = True,
                      build_table: bool = False,
                      delete_dataset_contents: bool = False,
                      delete_templates: bool = True) -> IngestionStatus:
        """
        [ALPHA] Perform a complete ingestion operation, from start to finish.

        Initiates an ingestion operation, polls the server to determine when the job
        has finished, and returns the outcome.

        Parameters
        ----------
        raise_errors: bool
            Whether ingestion errors raise exceptions (vs. simply reported in the results).
            Default: True
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
        job = self.build_objects_async(build_table=build_table,
                                       delete_dataset_contents=delete_dataset_contents,
                                       delete_templates=delete_templates)

        if raise_errors:
            self.poll_for_job_completion(job)
            status = self.status()
            if not status.success:
                raise JobFailureError(
                    message=f"Job succeeded but ingestion failed: {status.errors}",
                    job_id=job.job_id,
                    failure_reasons=status.errors
                )
        else:
            try:
                self.poll_for_job_completion(job)
                status = self.status()
            except JobFailureError as e:
                status = IngestionStatus.build({
                    "status": "Failure",
                    "errors": e.failure_reasons,
                })

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
        return JobSubmissionResponse.build(
            self.session.post_resource(path=path, json={}, params=params)
        )

    def poll_for_job_completion(self,
                                job: JobSubmissionResponse,
                                *,
                                timeout: Optional[float] = None,
                                polling_delay: Optional[float] = None
                                ) -> JobStatusResponse:
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
        JobStatusResponse
            A string representation of the status


        """
        kwargs = {}
        if timeout is not None:
            kwargs["timeout"] = timeout
        if polling_delay is not None:
            kwargs["polling_delay"] = polling_delay

        return _poll_for_job_completion(
            session=self.session,
            project_id=self.project_id,
            job=job,
            **kwargs
        )

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

    def build_from_file_links(self, file_links: Iterable["FileLink"]) -> Ingestion:
        """
        [ALPHA] Create an on-platform ingestion event based on the passed FileLink objects.

        Parameters
        ----------
        file_links: Iterable[FileLink]
            The files to ingest.

        """
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

        response = self.session.post_resource(path=self._get_path(), json=req)
        return self.build(response)

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
