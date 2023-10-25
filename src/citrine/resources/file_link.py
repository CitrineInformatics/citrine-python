"""A collection of FileLink objects."""
from deprecation import deprecated
import mimetypes
import os
from pathlib import Path
from logging import getLogger
from tempfile import TemporaryDirectory
from typing import Optional, Tuple, Union, List, Dict, Iterable, Sequence
from urllib.parse import urlparse, unquote_plus
from uuid import UUID

import requests
from boto3 import client as boto3_client
from boto3.session import Config
from botocore.exceptions import ClientError
from citrine._rest.collection import Collection
from citrine._rest.resource import GEMDResource
from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine._session import Session
from citrine._utils.functions import rewrite_s3_links_locally
from citrine._utils.functions import write_file_locally

from citrine.jobs.job import JobSubmissionResponse, _poll_for_job_completion
from citrine.resources.response import Response
from gemd.entity.dict_serializable import DictSerializableMeta
from gemd.entity.bounds.base_bounds import BaseBounds
from gemd.entity.file_link import FileLink as GEMDFileLink
from gemd.enumeration.base_enumeration import BaseEnumeration

logger = getLogger(__name__)


class SearchFileFilterTypeEnum(BaseEnumeration):
    """
    The type of the filter used to search for files.

    * SEARCH_BY_NAME:
        Search a file by name in a specific dataset,
        returns by default the last version or a specific one
    * SEARCH_BY_VERSION_ID:
        Search by a specific file version id
    * SEARCH_BY_DATASET_FILE_ID:
        Search either the last version or a specific version number for a specific dataset file id

    """

    NAME_SEARCH = "search_by_name"
    VERSION_ID_SEARCH = "search_by_version_id"
    DATASET_FILE_ID_SEARCH = "search_by_dataset_file_id"


class _Uploader:
    """Holds the many parameters that are generated and used during file upload."""

    def __init__(self):
        self.bucket = ''
        self.object_key = ''
        self.upload_id = ''
        self.region_name = ''
        self.aws_access_key_id = ''
        self.aws_secret_access_key = ''
        self.aws_session_token = ''
        self.s3_version = ''
        self.s3_endpoint_url = None
        self.s3_use_ssl = True
        self.s3_addressing_style = 'auto'


class FileProcessingType(BaseEnumeration):
    """The supported File Processing Types."""

    VALIDATE_CSV = "VALIDATE_CSV"


class FileProcessingData:
    """The base class of all File Processing related data implementations."""

    pass


class CsvColumnInfo(Serializable):
    """The info for a CSV Column, contains the name, recommended and exact bounds."""

    name = properties.String('name')
    """:str: name of the column"""
    bounds = properties.Object(BaseBounds, 'bounds')
    """:BaseBounds: recommended bounds of the column (might include some padding)"""
    exact_range_bounds = properties.Object(BaseBounds, 'exact_range_bounds')
    """:BaseBounds: exact bounds of the column"""

    def __init__(self, name: str, bounds: BaseBounds,
                 exact_range_bounds: BaseBounds):  # pragma: no cover
        self.name = name
        self.bounds = bounds
        self.exact_range_bounds = exact_range_bounds


class CsvValidationData(FileProcessingData, Serializable):
    """The resulting data from the processed CSV file."""

    columns = properties.Optional(properties.List(properties.Object(CsvColumnInfo)),
                                  'columns')
    """:Optional[List[CsvColumnInfo]]: all of the columns in the CSV"""
    record_count = properties.Integer('record_count')
    """:int: the number of rows in the CSV"""

    def __init__(self, columns: List[CsvColumnInfo],
                 record_count: int):  # pragma: no cover
        self.columns = columns
        self.record_count = record_count


class FileProcessingResult:
    """
    The results of a successful file processing operation.

    The type of the actual data depends on the specific processing type.
    """

    def __init__(self,
                 processing_type: FileProcessingType,
                 data: Union[Dict, FileProcessingData]):
        self.processing_type = processing_type
        self.data = data


class FileLinkMeta(DictSerializableMeta):
    """Metaclass for FileLink deserialization."""

    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cls.typ = properties.String('type', default="file_link", deserializable=False)


def _get_ids_from_url(url: str) -> Tuple[Optional[UUID], Optional[UUID]]:
    """Attempt to extract file_id and version_id from a URL."""
    parsed = urlparse(url)
    if len(parsed.query) > 0 or len(parsed.fragment) > 0:
        # Illegal modifiers
        return None, None
    split_path = urlparse(url).path.split('/')
    if len(split_path) >= 4 and split_path[-4] == 'files' and split_path[-2] == 'versions':
        file_id = split_path[-3]
        version_id = split_path[-1]
    elif len(split_path) >= 2 and split_path[-2] == 'files':
        file_id = split_path[-1]
        version_id = None
    else:
        file_id, version_id = None, None

    if file_id is not None:
        try:
            file_id = UUID(file_id)
            if version_id is not None:
                version_id = UUID(version_id)
        except ValueError:
            return None, None
    return file_id, version_id


class FileLink(
    GEMDResource['FileLink'],
    GEMDFileLink,
    metaclass=FileLinkMeta,
    typ=GEMDFileLink.typ
):
    """
    Resource that stores the name and url of an external file.

    Parameters
    ----------
    filename: str
        The name of the file.
    url: str
        URL that can be used to access the file.

    Attributes
    ----------
    uid: UUID
        Unique uuid4 identifier of this file; consistent across versions.
    version: UUID
        Unique uuid4 identifier of this version of this file
    version_number: Integer
        How many times this file has been uploaded;
        files are the "same" if the share a filename and dataset
    created_time: Datetime
        Time the file was created on platform.
    created_by: UUID
        Unique uuid4 identifier of this User who loaded this file
    mime_type: String
        Encoded string representing the type of the file (IETF RFC 2045)
    size: Integer
        Size in bytes of the file
    description: String
        A human-readable description of the file

    """

    # NOTE: skipping the "metadata" field since it appears to be unused
    # NOTE: skipping the "versioned_url" field since it is redundant
    # NOTE: skipping the "unversioned_url" field since it is redundant
    filename = properties.String('filename')
    url = properties.String('url')
    uid = properties.Optional(properties.UUID, 'id', serializable=False)
    version = properties.Optional(properties.UUID, 'version', serializable=False)
    created_time = properties.Optional(properties.Datetime, 'created_time', serializable=False)
    created_by = properties.Optional(properties.UUID, 'created_by', serializable=False)
    mime_type = properties.Optional(properties.String, 'mime_type', serializable=False)
    size = properties.Optional(properties.Integer, 'size', serializable=False)
    description = properties.Optional(properties.String, 'description', serializable=False)
    version_number = properties.Optional(properties.Integer, 'version_number', serializable=False)

    def __init__(self, filename: str, url: str):
        GEMDFileLink.__init__(self, filename, url)
        uid, version = _get_ids_from_url(url)
        if uid is not None:
            self.uid = uid
        if version is not None:
            self.version = version
        self.typ = FileLink.typ

    @classmethod
    def from_path(cls, path: Union[str, Path]) -> "FileLink":
        """Construct a FileLink from a local Path."""
        path = Path(path)  # In case it was a string
        return cls(filename=path.name, url=path.expanduser().absolute().as_uri())

    @property
    def name(self):
        """Attribute name is an alias for filename."""
        return self.filename

    @classmethod
    def _pre_build(cls, data: dict) -> dict:
        """Run data modification before building."""
        if 'url' in data and 'id' not in data:
            uid, version = _get_ids_from_url(data['url'])
            if uid is not None:
                data['id'] = str(uid)
            if version is not None:
                data['version'] = str(version)
        return data

    def __str__(self):
        return f'<File link {self.filename!r}>'


class FileCollection(Collection[FileLink]):
    """Represents the collection of all file links associated with a dataset."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/files'
    _collection_key = 'files'
    _resource = FileLink

    def __init__(self, project_id: UUID, dataset_id: UUID, session: Session):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.session = session

    def _get_path(self,
                  uid: Optional[Union[UUID, str]] = None,
                  *,
                  ignore_dataset: Optional[bool] = False,
                  version: Union[str, UUID] = None,
                  action: Union[str, Sequence[str]] = [],
                  query_terms: Dict[str, str] = {},) -> str:
        """Build the path for taking an action with a particular file version."""
        if version is not None:
            action = ['versions', version] + ([action] if isinstance(action, str) else action)
        return super()._get_path(uid=uid, ignore_dataset=ignore_dataset, action=action)

    def _get_path_from_file_link(self, file_link: FileLink,
                                 *,
                                 action: str = None) -> str:
        """Build the platform path for taking an action with a particular file link."""
        if not self._is_on_platform_url(file_link.url) or file_link.uid is None:
            raise ValueError("FileLink did not contain a Citrine platform file URL.")
        return self._get_path(uid=file_link.uid, version=file_link.version, action=action)

    def build(self, data: dict) -> FileLink:
        """Build an instance of FileLink."""
        # Use this chance to construct a URL from platform metadata
        if 'url' not in data:
            data['url'] = self._get_path(uid=data['id'], version=data['version'])

        return FileLink.build(data)

    def get(self,
            uid: Union[UUID, str],
            *,
            version: Optional[Union[UUID, str, int]] = None) -> FileLink:
        """
        Retrieve an on-platform FileLink from its filename or file uuid.

        Parameters
        ----------
        uid: Union[UUID, str]
            A representation of the FileLink (Citrine id or file name)
        version: Optional[UUID, str, int]
            The version, as a UUID or str(UUID) of the version_id or an int or
            str(int) of the version number.  If None, returns the file with the
            highest version number (most recent).

        Returns
        -------
        ResourceType
            An object with specified scope and uid

        """
        if not isinstance(uid, (str, UUID)):
            raise TypeError(f"File Link can only be resolved from str or UUID."
                            f"Instead got {type(uid)} {uid}.")
        if version is not None and not isinstance(version, (str, UUID, int)):
            raise TypeError(f"Version can only be resolved from str, int or UUID."
                            f"Instead got {type(uid)} {uid}.")

        if isinstance(uid, str):
            try:  # Check if the uid string is actually a UUID
                uid = UUID(uid)
            except ValueError:
                pass

        if isinstance(version, str):
            try:  # Check if the version string is actually a UUID
                version = UUID(version)
            except ValueError:
                try:  # Check if the version string is actually an int / version number
                    version = int(version)
                except ValueError:
                    raise ValueError(
                        f"Version {version} could not be converted to either an int or a UUID"
                    )

        if isinstance(uid, str):
            # Assume it's the filename on platform;
            if version is None or isinstance(version, int):
                file = self._search_by_file_name(dset_id=self.dataset_id,
                                                 file_name=uid,
                                                 file_version_number=version)
            else:  # We did our type checks earlier; version is a UUID
                file = self._search_by_file_version_id(file_version_id=version)
        else:  # We did our type checks earlier; uid is a UUID
            if isinstance(version, UUID):
                file = self._search_by_file_version_id(file_version_id=version)
            else:  # We did our type checks earlier; version is an int or None
                file = self._search_by_dataset_file_id(dataset_file_id=uid,
                                                       dset_id=self.dataset_id,
                                                       file_version_number=version)

        return file

    def upload(self, *, file_path: Union[str, Path], dest_name: str = None) -> FileLink:
        """
        Uploads a file to the dataset.

        Parameters
        ----------
        file_path: str, Path
            The path to the file on the local computer.
        dest_name: str, optional
            The name the file will have after being uploaded. If unspecified, the local name of
            the file will be used. That is, the file at "/Users/me/diagram.pdf" will be uploaded
            with the name "diagram.pdf". File names **must be unique** within a dataset. If a file
            is uploaded with the same `dest_name` as an existing file it will be considered
            a new version of the existing file.

        Returns
        -------
        FileLink
            The filename and url of the uploaded object.

        """
        file_path = Path(file_path).expanduser()
        if not file_path.is_file():
            raise ValueError(f"{file_path} is not a file.")

        if not dest_name:
            # Use the file name as a default dest_name
            dest_name = file_path.name

        uploader = self._make_upload_request(file_path, dest_name)
        uploader = self._upload_file(file_path, uploader)
        return self._complete_upload(dest_name, uploader)

    def _make_upload_request(self, file_path: Path, dest_name: str):
        """
        Make a request to the backend to upload a file. Uses mimetypes.guess_type.

        Parameters
        ----------
        file_path: Path
            The path to the file on the local computer.
        dest_name: str
            The name the file will have after being uploaded.

        Returns
        -------
        _Uploader
            Holds the parameters returned by the upload request, for later use.
            These must include region_name, aws_access_key_id, aws_secret_access_key,
            aws_session_token, bucket, object_key, & upload_id.

        """
        path = self._get_path(action="uploads")
        mime_type = self._mime_type(file_path)
        file_size = file_path.stat().st_size
        assert isinstance(file_size, int)
        upload_json = {
            'files': [
                {
                    'file_name': dest_name,
                    'mime_type': mime_type,
                    'size': file_size
                }
            ]
        }
        # POST request creates space in S3 for the file and returns AWS-related information
        # (such as temporary credentials) that allow the file to be uploaded.
        upload_request = self.session.post_resource(path=path, json=upload_json)
        uploader = _Uploader()

        # Extract all relevant information from the upload request
        try:

            uploader.region_name = upload_request['s3_region']
            uploader.aws_access_key_id = upload_request['temporary_credentials']['access_key_id']
            uploader.aws_secret_access_key = \
                upload_request['temporary_credentials']['secret_access_key']
            uploader.aws_session_token = upload_request['temporary_credentials']['session_token']
            uploader.bucket = upload_request['s3_bucket']
            uploader.object_key = upload_request['uploads'][0]['s3_key']
            uploader.upload_id = upload_request['uploads'][0]['upload_id']
            uploader.s3_endpoint_url = self.session.s3_endpoint_url
            uploader.s3_use_ssl = self.session.s3_use_ssl
            uploader.s3_addressing_style = self.session.s3_addressing_style

        except KeyError:
            raise RuntimeError("Upload initiation response is missing some fields: "
                               "{}".format(upload_request))
        return uploader

    def _search_by_file_name(self,
                             file_name: str,
                             dset_id: UUID,
                             file_version_number: Optional[int] = None
                             ) -> Optional[FileLink]:
        """
        Make a request to the backend to search a file by name.

        Note that you can specify a version number, in case you don't, it will
        return the last version by default.

        Parameters
        ----------
        file_name: str
            The name of the file.
        dset_id: UUID
            UUID that represents a dataset.
        file_version_number: Optional[int]
            As optional, you can send a specific version number.

        Returns
        -------
        FileLink
            All the data needed for a file.

        """
        path = self._get_path(action="search")

        search_json = {
            'fileSearchFilter':
                {
                    'type': SearchFileFilterTypeEnum.NAME_SEARCH.value,
                    'datasetId': str(dset_id),
                    'fileName': file_name,
                    'fileVersionNumber': file_version_number
                }
        }

        data = self.session.post_resource(path=path, json=search_json)

        return self.build(data['files'][0])

    def _search_by_file_version_id(self,
                                   file_version_id: UUID
                                   ) -> Optional[FileLink]:
        """
        Make a request to the backend to search a file by file version id.

        Parameters
        ----------
        file_version_id: UUID
            UUID that represents a file version id.

        Returns
        -------
        FileLink
            All the data needed for a file.

        """
        path = self._get_path(action="search")

        search_json = {
            'fileSearchFilter': {
                'type': SearchFileFilterTypeEnum.VERSION_ID_SEARCH.value,
                'fileVersionUuid': str(file_version_id)
            }
        }

        data = self.session.post_resource(path=path, json=search_json)

        return self.build(data['files'][0])

    def _search_by_dataset_file_id(self,
                                   dataset_file_id: UUID,
                                   dset_id: UUID,
                                   file_version_number: Optional[int] = None
                                   ) -> Optional[FileLink]:
        """
        Make a request to the backend to search a file by dataset file id.

        Note that you can specify a version number, in case you don't, it will
        return the last version by default.

        Parameters
        ----------
        dataset_file_id: UUID
            UUID that represents a dataset file id.
        dset_id: UUID
            UUID that represents a dataset.
        file_version_number: Optional[int]
            As optional, you can send a specific version number

        Returns
        -------
        FileLink
            All the data needed for a file.

        """
        path = self._get_path(action="search")

        search_json = {
            'fileSearchFilter': {
                'type': SearchFileFilterTypeEnum.DATASET_FILE_ID_SEARCH.value,
                'datasetId': str(dset_id),
                'datasetFileId': str(dataset_file_id),
                'fileVersionNumber': file_version_number
            }
        }

        data = self.session.post_resource(path=path, json=search_json)

        return self.build(data['files'][0])

    @staticmethod
    def _mime_type(file_path: Path):
        # This string coercion is for supporting pathlib.Path objects in python < 3.8
        mime_type = mimetypes.guess_type(str(file_path))[0]
        if mime_type is None:
            mime_type = "application/octet-stream"
        return mime_type

    @staticmethod
    def _upload_file(file_path: Path, uploader: _Uploader):
        """
        Upload a file to S3.

        Parameters
        ----------
        file_path: Path
            The path to the file on the local computer.
        uploader: _Uploader
            Holds the parameters returned by the upload request.

        Returns
        -------
        _Uploader
            The input uploader object with its s3_version field now populated.

        """
        additional_s3_opts = {
            'use_ssl': uploader.s3_use_ssl,
            'config': Config(s3={'addressing_style': uploader.s3_addressing_style})
        }

        if uploader.s3_endpoint_url is not None:
            additional_s3_opts['endpoint_url'] = uploader.s3_endpoint_url

        s3_client = boto3_client('s3',
                                 region_name=uploader.region_name,
                                 aws_access_key_id=uploader.aws_access_key_id,
                                 aws_secret_access_key=uploader.aws_secret_access_key,
                                 aws_session_token=uploader.aws_session_token,
                                 **additional_s3_opts)
        with file_path.open(mode='rb') as f:
            try:
                # NOTE: This is only using the simple PUT logic, not the more sophisticated
                # multipart upload approach that is also available (providing parallel
                # uploads, etc).
                upload_response = s3_client.put_object(
                    Bucket=uploader.bucket,
                    Key=uploader.object_key,
                    Body=f,
                    Metadata={"X-Citrine-Upload-Id": uploader.upload_id})
            except ClientError as e:
                raise RuntimeError(f"Upload of file {file_path} failed with the following "
                                   f"exception: {e}")
        uploader.s3_version = upload_response['VersionId']
        return uploader

    def _complete_upload(self, dest_name: str, uploader: _Uploader):
        """
        Indicate that the upload has finished and determine the file URL.

        Parameters
        ----------
        dest_name: str
            The name the file will have after being uploaded.
        uploader: _Uploader
            Holds the parameters returned by the upload request and the upload response.

        Returns
        -------
        FileLink
            The filename and url of the uploaded object.

        """
        url = self._get_path(action=["uploads", uploader.upload_id, "complete"])
        complete_response = self.session.put_resource(path=url,
                                                      json={'s3_version': uploader.s3_version})

        try:
            file_id = complete_response['file_info']['file_id']
            version_id = complete_response['file_info']['version']
        except KeyError:
            raise RuntimeError("Upload completion response is missing some "
                               "fields: {}".format(complete_response))

        return self.build({"filename": dest_name, "id": file_id, "version": version_id})

    def download(self, *, file_link: Union[str, UUID, FileLink], local_path: Union[str, Path]):
        """
        Download the file associated with a given FileLink to the local computer.

        Parameters
        ----------
        file_link: FileLink, str, UUID
            Resource referencing the file.
        local_path: str, Path
            Path to save file on the local computer. If `local_path` is a directory,
            then the filename of this FileLink object will be appended to the path.

        """
        file_link = self._resolve_file_link(file_link)

        if isinstance(local_path, str):
            directory, filename = os.path.split(local_path)
            if len(filename) == 0:  # the string ended with /
                final_path = Path(directory) / file_link.filename
            else:
                final_path = Path(directory) / filename
        elif local_path.is_dir():
            final_path = local_path / file_link.filename
        else:
            final_path = local_path

        response_content = self.read(file_link=file_link)
        write_file_locally(response_content, final_path)

    def read(self, *, file_link: Union[str, UUID, FileLink]) -> bytes:
        """
        Read the file associated with a given FileLink.

        Parameters
        ----------
        file_link: FileLink, str, UUID
            Resource referencing the file.

        Returns
        -------
        I/O stream
            The contents of the file.

        """
        file_link = self._resolve_file_link(file_link)

        if self._is_local_url(file_link.url):  # Read the local file
            path = Path(unquote_plus(urlparse(file_link.url).path))
            return path.read_bytes()

        if self._is_external_url(file_link.url):  # Pull it from where ever it lives
            final_url = file_link.url
        else:
            # The "/content-link" route returns a pre-signed url to download the file.
            content_link = self._get_path_from_file_link(file_link, action='content-link')
            content_link_response = self.session.get_resource(content_link)
            pre_signed_url = content_link_response['pre_signed_read_link']
            final_url = rewrite_s3_links_locally(pre_signed_url, self.session.s3_endpoint_url)

        download_response = requests.get(final_url)
        return download_response.content

    @deprecated(deprecated_in="2.4.0",
                removed_in="3.0.0",
                details="The process file protocol is deprecated "
                        "in favor of ingest()")
    def process(self, *, file_link: Union[FileLink, str, UUID],
                processing_type: FileProcessingType,
                wait_for_response: bool = True,
                timeout: float = 2 * 60,
                polling_delay: float = 1.0) -> Union[JobSubmissionResponse,
                                                     Dict[FileProcessingType,
                                                          FileProcessingResult]]:
        """
        Start a File Processing async job, returning a pollable job response.

        Parameters
        ----------
        file_link: FileLink, str, or UUID
            The file to process.
        processing_type: FileProcessingType
            The type of file processing to invoke.
        wait_for_response: bool
            Whether to wait for a result, vs. just return a job handle.  Default: True
        timeout: float
            How long to poll for the result before giving up. This is expressed in
            (fractional) seconds.  Default: 120 seconds.
        polling_delay: float
            How long to delay between each polling retry attempt.  Default: 1 second.

        Returns
        -------
        JobSubmissionResponse
            A JobSubmissionResponse which can be used to poll for the result.

        """
        if self._is_external_url(file_link.url):
            raise ValueError(f"Only on-platform resources can be processed. "
                             f"Passed URL {file_link.url}.")
        file_link = self._resolve_file_link(file_link)

        params = {"processing_type": processing_type.value}
        response = self.session.put_resource(
            self._get_path_from_file_link(file_link, action="processed"),
            json={},
            params=params
        )
        job = JobSubmissionResponse.build(response)
        logger.info('Build job submitted with job ID {}.'.format(job.job_id))

        if wait_for_response:
            return self.poll_file_processing_job(file_link=file_link,
                                                 processing_type=processing_type,
                                                 job_id=job.job_id, timeout=timeout,
                                                 polling_delay=polling_delay)
        else:
            return job

    @deprecated(deprecated_in="2.4.0",
                removed_in="3.0.0",
                details="The process file protocol is deprecated "
                        "in favor of ingest()")
    def poll_file_processing_job(self, *, file_link: FileLink,
                                 processing_type: FileProcessingType,
                                 job_id: UUID,
                                 timeout: float = 2 * 60,
                                 polling_delay: float = 1.0) -> Dict[FileProcessingType,
                                                                     FileProcessingResult]:
        """
        Poll for the result of the file processing task.

        Parameters
        ----------
        file_link: FileLink
            The file to process.
        processing_type: FileProcessingType
            The processing algorithm to apply.
        job_id: UUID
           The background job ID to poll for.
        timeout:
            How long to poll for the result before giving up. This is expressed in
            (fractional) seconds.
        polling_delay:
            How long to delay between each polling retry attempt.

        Returns
        -------
        None
           This method will raise an appropriate exception if the job failed, else
           it will return None to indicate the job was successful.

        """
        # Poll for job completion - this will raise an error if the job failed
        _poll_for_job_completion(self.session, self.project_id, job_id, timeout=timeout,
                                 polling_delay=polling_delay)

        return self.file_processing_result(file_link=file_link, processing_types=[processing_type])

    @deprecated(deprecated_in="2.4.0",
                removed_in="3.0.0",
                details="The process file protocol is deprecated "
                        "in favor of ingest()")
    def file_processing_result(self, *,
                               file_link: FileLink,
                               processing_types: List[FileProcessingType]) -> \
            Dict[FileProcessingType, FileProcessingResult]:
        """
        Return the file processing result for the given file link and processing type.

        Parameters
        ----------
        file_link: FileLink
            The file to process
        processing_types: FileProcessingType
            A list of the particular file processing types to retrieve

        Returns
        -------
        Map[FileProcessingType, FileProcessingResult]
            The file processing results, mapped by processing type.

        """
        processed_results_path = self._get_path_from_file_link(file_link, action="processed")

        params = []
        for proc_type in processing_types:
            params.append(('processing_type', proc_type.value))

        response = self.session.get_resource(processed_results_path, params=params)
        results_json = response['results']
        results = {}
        for result_json in results_json:
            processing_type = FileProcessingType[result_json['processing_type']]
            data = result_json['data']

            if processing_type == FileProcessingType.VALIDATE_CSV:
                data = CsvValidationData.build(data)

            result = FileProcessingResult(processing_type, data)
            results[processing_type] = result

        return results

    def ingest(self,
               files: Iterable[Union[FileLink, Path, str]],
               *,
               upload: bool = False,
               raise_errors: bool = True,
               build_table: bool = False,
               delete_dataset_contents: bool = False,
               delete_templates: bool = True,
               timeout: float = None,
               polling_delay: Optional[float] = None
               ) -> "IngestionStatus":  # noqa: F821
        """
        [ALPHA] Ingest a set of CSVs and/or Excel Workbooks formatted per the gemd-ingest protocol.

        Parameters
        ----------
        files: List[FileLink, Path, or str]
            A list of files from which GEMD objects should be built.
            A FileLink must contain an absolute URL or a relative path for an on-platform resource.
            Strings must be resolvable to a FileLink; if resolution fails, an exception is thrown.
            * If upload is False, an attempt is made to resolve it to an on-platform resource.
            * If upload is True, resolves locally first, and falls back to on-platform.
        upload: bool
            If the files are off-platform references, upload them first.
            Defaults to False, in which case an off-platform resource raises an error.
            A file is off-platform if it has an absolute URL and that URL is not for the
            citrine platform.
            For example, https://example.com/file.csv is off-platform, and would be
            uploaded to platform and ingested if upload is True.
        raise_errors: bool
            Whether ingestion errors raise exceptions (vs. simply reported in the results).
            Default: True
        build_table: bool
            Whether to trigger a regeneration of the table config and building the table
            after ingestion.  Default: False
        delete_dataset_contents: bool
            Whether to delete old objects prior to creating new ones.  Default: False
        delete_templates: bool
            Whether to delete old templates if deleting old objects.  Default: True
        timeout: Optional[float]
            Amount of time to wait on the job (in seconds) before giving up. Note that
            this number has no effect on the underlying job itself, which can also time
            out server-side.
        polling_delay: Optional[float]
            How long to delay between each polling retry attempt.


        Returns
        ----------
        IngestionStatus
            The result of the ingestion operation.

        """
        from citrine.resources.ingestion import IngestionCollection

        def resolve_with_local(candidate: Union[FileLink, Path, str]) -> FileLink:
            """Resolve Path, str or FileLink to an absolute reference."""
            if upload:
                if not isinstance(candidate, GEMDFileLink):
                    try:
                        absolute = Path(candidate).expanduser().resolve(strict=True)
                        return FileLink(filename=absolute.name, url=absolute.as_uri())
                    except FileNotFoundError as e:
                        if isinstance(candidate, Path):  # Unresolvable path passed
                            raise e
            elif isinstance(candidate, Path):
                raise TypeError("Path objects are only valid when upload=True.")

            return self._resolve_file_link(candidate)  # It was a FileLink or unresolvable string

        resolved = []
        for file in files:
            resolved_file = resolve_with_local(file)
            if resolved_file not in resolved:  # Remove duplicates
                resolved.append(resolved_file)

        onplatform = [f for f in resolved if self._is_on_platform_url(f.url)]
        offplatform = [f for f in resolved if not self._is_on_platform_url(f.url)]

        if upload:
            with TemporaryDirectory() as downloads:
                for file_link in offplatform:
                    path = Path(downloads) / file_link.filename
                    self.download(file_link=file_link, local_path=path)
                    onplatform.append(self.upload(file_path=path, dest_name=file_link.filename))
        elif len(offplatform) > 0:
            raise ValueError(f"All files must be on-platform to load them.  "
                             f"The following are not: {offplatform}")

        ingestion_collection = IngestionCollection(project_id=self.project_id,
                                                   dataset_id=self.dataset_id,
                                                   session=self.session)
        ingestion = ingestion_collection.build_from_file_links(
            file_links=onplatform,
            raise_errors=raise_errors
        )
        return ingestion.build_objects(
            build_table=build_table,
            delete_dataset_contents=delete_dataset_contents,
            delete_templates=delete_templates,
            timeout=timeout,
            polling_delay=polling_delay
        )

    def delete(self, file_link: FileLink):
        """
        Delete the file associated with a given FileLink from the database.

        Parameters
        ----------
        file_link: FileLink
            Resource referencing the external file.

        """
        if not self._is_on_platform_url(file_link.url):
            raise ValueError(f"Only platform resources can be deleted; passed URL {file_link.url}")
        file_id = _get_ids_from_url(file_link.url)[0]
        if file_id is None:
            raise ValueError(f"URL was malformed for local resources; passed URL {file_link.url}")
        data = self.session.delete_resource(self._get_path(file_id))
        return Response(body=data)

    def _resolve_file_link(self, identifier: Union[str, UUID, FileLink]) -> FileLink:
        """Generate the FileLink object referenced by the passed argument."""
        if isinstance(identifier, GEMDFileLink):
            if not isinstance(identifier, FileLink):  # Up-convert type with existing info
                update = FileLink(filename=identifier.filename, url=identifier.url)

                if self._is_on_platform_url(update.url):
                    if update.uid is None:
                        raise ValueError(f"URL was malformed for platform resources; "
                                         f"passed URL {update.url}")
                    else:  # Validate that it's a real record
                        update = self.get(uid=update.uid, version=update.version)
                        if update.filename != identifier.filename:
                            raise ValueError(
                                f"Name mismatch between link ({identifier.filename}) "
                                f"and platform ({update.filename})"
                            )
                    identifier = update

            return identifier  # Passthrough since it's as full as it can get
        elif isinstance(identifier, str):
            if self._is_on_platform_url(identifier):  # It's either a filename or URL
                file_id, version_id = _get_ids_from_url(identifier)
                if file_id is None:  # Try it as a name or a stand-alone UID
                    return self.get(identifier)
                else:  # We got a file UID (and possibly a version UID) from a URL
                    return self.get(uid=file_id, version=version_id)
            else:  # Assume it's an absolute URL
                filename = urlparse(identifier).path.split('/')[-1]
                return FileLink(filename=filename, url=identifier)
        elif isinstance(identifier, UUID):  # File UID
            return self.get(uid=identifier)
        else:
            raise TypeError(f"File Link can only be resolved from str, or UUID."
                            f"Instead got {type(identifier)} {identifier}.")

    def _is_external_url(self, url: str):
        """Check if the URL is absolute and not associated with this platform instance."""
        parsed = urlparse(url)
        if len(parsed.scheme) == 0 or len(parsed.netloc) == 0:
            # Relative
            return False

        return urlparse(self._get_path()).netloc != parsed.netloc

    @staticmethod
    def _is_local_url(url: str):
        """Check if the URL is for a local file."""
        parsed = urlparse(url)
        return parsed.scheme == "file"

    def _is_on_platform_url(self, url: str):
        """Check if the URL is for an on-platform record."""
        return not self._is_external_url(url) and not self._is_local_url(url)
