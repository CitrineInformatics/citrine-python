from typing import Optional, Iterator, Iterable
from uuid import UUID

from citrine._rest.collection import Collection
from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine._session import Session
from citrine.exceptions import CitrineException, BadRequest
from citrine.jobs.job import JobSubmissionResponse, JobFailureError, _poll_for_job_completion
from citrine.resources.api_error import ApiError, ValidationError
from gemd.enumeration.base_enumeration import BaseEnumeration


class IngestionStatusType(BaseEnumeration):
    """[ALPHA] State of the ingestion process."""

    INGESTION_CREATED = "ingestion_created"


class IngestionErrorFamily(BaseEnumeration):
    """[ALPHA] What class of ingest error was encountered."""

    FILE = "file"
    STRUCTURE = "structure"
    DATA = "data"
    UNKNOWN = "unknown"


class IngestionErrorType(BaseEnumeration):
    """[ALPHA] What ingest error was encountered."""

    FILE_EXTENSION_NOT_SUPPORTED = "file_extension_not_supported"
    MISSING_TYPE_HEADER = "missing_type_header"
    MISSING_RAW_FOR_INGREDIENT = "missing_raw_for_ingredient"
    DUPLICATED_MATERIAL = "duplicated_material"
    REGISTERING_OBJECTS_ERROR = "registering_objects_error"
    MISSING_ASPECT_TYPE = "missing_aspect_type"
    INVALID_DUPLICATE_NAME = "invalid_duplicate_name"
    INVALID_UNITS_ON_ASPECT = "invalid_units_on_aspect"
    INVALID_BASIS_ON_ASPECT = "invalid_basis_on_aspect"
    INVALID_FRACTION_ON_ASPECT = "invalid_fraction_on_aspect"
    INVALID_TYPE_HINT_ON_ASPECT = "invalid_type_hint_on_aspect"
    CATEGORICAL_OUTSIDE_BOUNDS_ERROR = "categorical_outside_bounds_error"
    INTEGER_OUTSIDE_BOUNDS_ERROR = "integer_outside_bounds_error"
    REAL_OUTSIDE_BOUNDS_ERROR = "real_outside_bounds_error"
    INVALID_PROCESS_REFERENCE = "invalid_process_reference"
    COLLIDING_ID = "colliding_id"
    UNKNOWN_ERROR = "unknown_error"


class IngestionErrorLevel(BaseEnumeration):
    """[ALPHA] Severity of the issue encountered."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class IngestionErrorTrace(Resource['IngestionErrorTrace']):
    """[ALPHA] Detailed information about an ingestion issue."""

    family = properties.Enumeration(IngestionErrorFamily, "family")
    error_type = properties.Enumeration(IngestionErrorType, "error_type")
    level = properties.Enumeration(IngestionErrorLevel, "level")
    msg = properties.String("msg")
    dataset_file_id = properties.Optional(properties.UUID(), "dataset_file_id", default=None)
    file_version_uuid = properties.Optional(properties.UUID(), "file_version_uuid", default=None)
    row_number = properties.Optional(properties.Integer(), "row_number", default=None)
    column_number = properties.Optional(properties.Integer(), "column_number", default=None)

    def __init__(self,
                 msg,
                 level=IngestionErrorLevel.ERROR,
                 *,
                 family=IngestionErrorFamily.UNKNOWN,
                 error_type=IngestionErrorType.UNKNOWN_ERROR,
                 dataset_file_id=dataset_file_id.default,
                 file_version_uuid=file_version_uuid.default,
                 row_number=row_number.default,
                 column_number=column_number.default,
                 ):
        self.msg = msg
        self.level = level
        self.family = family
        self.error_type = error_type
        self.dataset_file_id = dataset_file_id
        self.file_version_uuid = file_version_uuid
        self.row_number = row_number
        self.column_number = column_number

    @classmethod
    def from_validation_error(cls, source: ValidationError) -> "IngestionErrorTrace":
        """[ALPHA] Generate an IngestionErrorTrace from a ValidationError."""
        return cls(
            msg=source.failure_message,
            level=IngestionErrorLevel.ERROR,
        )

    def __str__(self):
        return f"{self!r}: {self.msg}"

    def __repr__(self):
        coords = ", ".join([x for x in (self.column_number, self.row_number) if x is not None])
        return f"<{self.level}: {self.error_type}{f' {coords}' if len(coords) else ''}>"


class IngestionException(CitrineException):
    """
    [ALPHA] An exception that contains details of a failed ingestion.

    Attributes
    ----------
    uid: Optional[UUID]
    errors: List[IngestionErrorTrace]

    """

    uid = properties.Optional(properties.UUID(), 'ingestion_id', default=None)
    status = properties.Enumeration(IngestionStatusType, "status")
    errors = properties.List(properties.Object(IngestionErrorTrace), "errors")

    def __init__(self,
                 *,
                 uid: Optional[UUID] = uid.default,
                 errors: Iterable[IngestionErrorTrace]):
        errors_ = list(errors)
        message = '; '.join(str(e) for e in errors_)
        super().__init__(message)
        self.uid = uid
        self.errors = errors_

    @classmethod
    def from_status(cls, source: "IngestionStatus") -> "IngestionException":
        """[ALPHA] Build an IngestionException from an IngestionStatus."""
        return cls(uid=source.uid, errors=source.errors)

    @classmethod
    def from_api_error(cls, source: ApiError) -> "IngestionException":
        """[ALPHA] Build an IngestionException from an ApiError."""
        if len(source.validation_errors) > 0:
            return cls(errors=[IngestionErrorTrace.from_validation_error(x)
                               for x in source.validation_errors])
        else:
            return cls(errors=[IngestionErrorTrace(msg=source.message)])


class IngestionStatus(Resource['IngestionStatus']):
    """
    [ALPHA] An object that represents the outcome of an ingestion event.

    Attributes
    ----------
    uid: String
    status: IngestionStatusType
    errors: List[IngestionErrorTrace]

    """

    uid = properties.Optional(properties.UUID(), 'ingestion_id', default=None)
    status = properties.Enumeration(IngestionStatusType, "status")
    errors = properties.List(properties.Object(IngestionErrorTrace), "errors")

    def __init__(self,
                 *,
                 uid: Optional[UUID] = uid.default,
                 status: IngestionStatusType = IngestionStatusType.INGESTION_CREATED,
                 errors: Iterable[IngestionErrorTrace]):
        self.uid = uid
        self.status = status
        self.errors = list(errors)

    @property
    def success(self) -> bool:
        """Whether the Ingestion operation was error-free."""
        return len(self.errors) == 0

    @classmethod
    def from_exception(cls, exception: IngestionException) -> "IngestionStatus":
        """[ALPHA] Build an IngestionStatus from an IngestionException."""
        return cls(uid=exception.uid, errors=exception.errors)


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
                      delete_templates: bool = True,
                      timeout: float = None,
                      polling_delay: Optional[float] = None
                      ) -> IngestionStatus:
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
        timeout: Optional[float]
            Amount of time to wait on the job (in seconds) before giving up. Note that
            this number has no effect on the underlying job itself, which can also time
            out server-side.
        polling_delay: Optional[float]
            How long to delay between each polling retry attempt.

        Returns
        ----------
        JobSubmissionResponse
            The object for the submitted job

        """
        try:
            job = self.build_objects_async(build_table=build_table,
                                           delete_dataset_contents=delete_dataset_contents,
                                           delete_templates=delete_templates)
        except IngestionException as e:
            if self.raise_errors:
                raise e
            else:
                return IngestionStatus.from_exception(e)

        status = self.poll_for_job_completion(job, timeout=timeout, polling_delay=polling_delay)

        if self.raise_errors and not status.success:
            raise IngestionException.from_status(status)

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
                raise IngestionException.from_api_error(e.api_error)
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

    def __init__(self, errors: Iterable[IngestionErrorTrace]):
        self.errors = list(errors)
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
                "status": IngestionStatusType.INGESTION_CREATED,
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
                if e.api_error.validation_errors:
                    errors = [IngestionErrorTrace.from_validation_error(error)
                              for error in e.api_error.validation_errors]
                else:
                    errors = [IngestionErrorTrace(msg=e.api_error.message)]
                if raise_errors:
                    raise IngestionException(errors=errors)
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
