"""A collection of FileLink objects."""
import mimetypes
import os
from enum import Enum
from logging import getLogger
from typing import Iterable, Optional, Tuple, Union, List, Dict
from urllib.parse import urlparse, quote
from uuid import UUID

import requests
from boto3 import client as boto3_client
from boto3.session import Config
from botocore.exceptions import ClientError
from citrine._rest.collection import Collection
from citrine._rest.resource import Resource
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.properties import Optional as PropertyOptional
from citrine._serialization.properties import String, Object, Integer
from citrine._serialization.serializable import Serializable
from citrine._session import Session
from citrine._utils.functions import rewrite_s3_links_locally
from citrine._utils.functions import write_file_locally, format_escaped_url
from citrine.jobs.job import JobSubmissionResponse, _poll_for_job_completion
from citrine.resources.response import Response
from gemd.entity.bounds.base_bounds import BaseBounds
from gemd.entity.file_link import FileLink as GEMDFileLink

logger = getLogger(__name__)


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


class FileProcessingType(Enum):
    """The supported File Processing Types."""

    VALIDATE_CSV = "VALIDATE_CSV"


class FileProcessingData:
    """The base class of all File Processing related data implementations."""

    pass


class CsvColumnInfo(Serializable):
    """The info for a CSV Column, contains the name, recommended and exact bounds."""

    name = String('name')
    """:str: name of the column"""
    bounds = Object(BaseBounds, 'bounds')
    """:BaseBounds: recommended bounds of the column (might include some padding)"""
    exact_range_bounds = Object(BaseBounds, 'exact_range_bounds')
    """:BaseBounds: exact bounds of the column"""

    def __init__(self, name: String, bounds: BaseBounds,
                 exact_range_bounds: BaseBounds):  # pragma: no cover
        self.name = name
        self.bounds = bounds
        self.exact_range_bounds = exact_range_bounds


class CsvValidationData(FileProcessingData, Serializable):
    """The resulting data from the processed CSV file."""

    columns = PropertyOptional(PropertyList(Object(CsvColumnInfo)), 'columns',
                               override=True)
    """:Optional[List[CsvColumnInfo]]: all of the columns in the CSV"""
    record_count = Integer('record_count')
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

    def __init__(self, processing_type: FileProcessingType, data: Union[Dict,
                                                                        FileProcessingData]):
        self.processing_type = processing_type
        self.data = data


class FileLink(Resource['FileLink'], GEMDFileLink):
    """
    Resource that stores the name and url of an external file.

    Parameters
    ----------
    filename: str
        The name of the file.
    url: str
        URL that can be used to access the file.

    """

    filename = String('filename', override=True)
    url = String('url', override=True)
    typ = String('type')

    def __init__(self, filename: str, url: str):
        GEMDFileLink.__init__(self, filename, url)
        self.typ = GEMDFileLink.typ

    @property
    def name(self):
        """Attribute name is an alias for filename."""
        return self.filename

    def __str__(self):
        return '<File link {!r}>'.format(self.filename)

    def as_dict(self) -> dict:
        """Dump to a dictionary (useful for interoperability with gemd)."""
        return self.dump()


class FileCollection(Collection[FileLink]):
    """Represents the collection of all file links associated with a dataset."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/files'
    _individual_key = 'file'
    _collection_key = 'files'
    _resource = FileLink

    def __init__(self, project_id: UUID, dataset_id: UUID, session: Session):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.session = session

    def _get_versioned_path(self,
                            file_id: Union[str, UUID],
                            version_id: Union[str, UUID],
                            *,
                            action: str = None) -> str:
        """Build the path for taking an action with a particular file version."""
        base = urlparse(self._get_path(file_id))
        new_path = base.path.split('/')
        new_path.extend([quote(x) for x in ('versions', str(version_id))])
        if action is not None:
            new_path.append(quote(action))

        return base._replace(path='/'.join(new_path)).geturl()

    def _get_path_from_file_link(self, file_link: FileLink,
                                 *,
                                 action: str = None) -> str:
        """Build the path for taking an action with a particular file link."""
        # Use this sessions project/dataset credentials and the URL's file / version
        parsed = urlparse(file_link.url)
        file_id = parsed.path.split('/')[-3]
        version_id = parsed.path.split('/')[-1]
        # The "/content-link" route returns a pre-signed url to download the file.
        return self._get_versioned_path(file_id, version_id, action=action)

    def build(self, data: dict) -> FileLink:
        """Build an instance of FileLink."""
        return FileLink.build(data)

    def _fetch_page(self,
                    page: Optional[int] = None,
                    per_page: Optional[int] = None) -> Tuple[Iterable[FileLink], str]:
        """
        List all visible files in the collection.

        Parameters
        ---------
        page: int, optional
            The "page" number of results to list. Default is the first page, which is 1.
        per_page: int, optional
            Max number of results to return for each call. Default is 20.

        Returns
        -------
        Iterable[FileLink]
            FileLink objects in this collection.
        str
            The next uri if one is available, empty string otherwise

        """
        path = self._get_path()
        params = {}
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page

        response = self.session.get_resource(path=path, params=params)
        collection = response[self._collection_key]
        return collection, ""

    def _build_collection_elements(self, collection):
        for file in collection:
            yield self.build(self._as_dict_from_resource(file))

    def _as_dict_from_resource(self, file: dict):
        """
        Convert a file link resource downloaded from the API into a FileLink dictionary.

        This is necessary because the database resource contains additional information that is
        not in the FileLink object, such as file size and the id of the user who uploaded the file.

        Parameters
        ---------
        file: dict
            A JSON dictionary corresponding to the file link as it is saved in the database.

        Returns
        -------
        dict
            A dictionary that can be built into a FileLink object.

        """
        filename = file['filename']
        file_id = file['id']
        version_id = file['version']

        file_dict = {
            'url': self._get_versioned_path(file_id, version_id),
            'filename': filename,
            'type': GEMDFileLink.typ
        }
        return file_dict

    def upload(self, *, file_path: str, dest_name: str = None) -> FileLink:
        """
        Uploads a file to the dataset.

        Parameters
        ----------
        file_path: str
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
        if not os.path.isfile(file_path):
            raise ValueError("No file at specified path {}".format(file_path))

        if not dest_name:
            # Use the file name as a default dest_name
            dest_name = os.path.basename(file_path)

        uploader = self._make_upload_request(file_path, dest_name)
        uploader = self._upload_file(file_path, uploader)
        return self._complete_upload(dest_name, uploader)

    def _make_upload_request(self, file_path: str, dest_name: str):
        """
        Make a request to the backend to upload a file. Uses mimetypes.guess_type.

        Parameters
        ----------
        file_path: str
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
        path = self._get_path() + "/uploads"
        # This string coercion is for supporting pathlib.Path objects in python 3.6
        mime_type = self._mime_type(str(file_path))
        file_size = os.stat(file_path).st_size
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

    @staticmethod
    def _mime_type(file_path: str):
        mime_type = mimetypes.guess_type(file_path)[0]
        if mime_type is None:
            mime_type = "application/octet-stream"
        return mime_type

    @staticmethod
    def _upload_file(file_path: str, uploader: _Uploader):
        """
        Upload a file to S3.

        Parameters
        ----------
        file_path: str
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
        with open(file_path, 'rb') as f:
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
                raise RuntimeError("Upload of file {} failed with the following "
                                   "exception: {}".format(file_path, e))
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
        path = self._get_path() + format_escaped_url("/uploads/{}/complete", uploader.upload_id)
        complete_response = self.session.put_resource(path=path,
                                                      json={'s3_version': uploader.s3_version})

        try:
            file_id = complete_response['file_info']['file_id']
            version = complete_response['file_info']['version']
        except KeyError:
            raise RuntimeError("Upload completion response is missing some "
                               "fields: {}".format(complete_response))

        url = self._get_versioned_path(file_id, version)
        return FileLink(filename=dest_name, url=url)

    def download(self, *, file_link: Union[str, UUID, FileLink], local_path: str):
        """
        Download the file associated with a given FileLink to the local computer.

        Parameters
        ----------
        file_link: FileLink, str, UUID
            Resource referencing the file.
        local_path: str
            Path to save file on the local computer. If `local_path` is a directory,
            then the filename of this FileLink object will be appended to the path.

        """
        file_link = self._resolve_file_link(file_link)

        directory, filename = os.path.split(local_path)
        if not filename:
            filename = file_link.filename
        local_path = os.path.join(directory, filename)

        if self._is_external_url(file_link.url):  # Pull it from where ever it lives
            final_url = file_link.url
        elif self._validate_filelink_url(file_link.url):
            # The "/content-link" route returns a pre-signed url to download the file.
            content_link = self._get_path_from_file_link(file_link, action='content-link')
            content_link_response = self.session.get_resource(content_link)
            pre_signed_url = content_link_response['pre_signed_read_link']
            final_url = rewrite_s3_links_locally(pre_signed_url, self.session.s3_endpoint_url)
        else:  # Unrecognized
            raise ValueError(f"URL was malformed for a local file resource ({file_link.url}).")

        download_response = requests.get(final_url)
        write_file_locally(download_response.content, local_path)

    def process(self, *, file_link: Union[FileLink, str, UUID],
                processing_type: FileProcessingType,
                wait_for_response: bool = True,
                timeout: float = 2 * 60,
                polling_delay: float = 1.0) -> Union[JobSubmissionResponse,
                                                     Dict[FileProcessingType,
                                                          FileProcessingResult]]:
        """
        Start a File Processing async job, returning a pollable job response.

        :param file_link: The file to process.
        :param processing_type:  The type of file processing to invoke.
        :return: A JobSubmissionResponse which can be used to poll for the result.
        """
        file_link = self._resolve_file_link(file_link)
        if not self._validate_filelink_url(file_link.url):
            raise ValueError(f"Only on-platform resources can be processed. "
                             f"Passed URL {file_link.url}.")

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

    def poll_file_processing_job(self, *, file_link: FileLink,
                                 processing_type: FileProcessingType,
                                 job_id: UUID,
                                 timeout: float = 2 * 60,
                                 polling_delay: float = 1.0) -> Dict[FileProcessingType,
                                                                     FileProcessingResult]:
        """
        [ALPHA] Poll for the result of the file processing task.

        Parameters
        ----------
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

    def delete(self, file_link: FileLink):
        """
        Delete the file associated with a given FileLink from the database.

        Parameters
        ----------
        file_link: FileLink
            Resource referencing the external file.

        """
        if self._is_external_url(file_link.url):
            raise ValueError(f"Only local resources can be deleted; passed URL {file_link.url}")
        if not self._validate_filelink_url(file_link.url):
            raise ValueError(f"URL was malformed for local resources; passed URL {file_link.url}")
        split_url = file_link.url.split('/')
        file_id = split_url[-3]
        data = self.session.delete_resource(self._get_path(file_id))
        return Response(body=data)

    def _resolve_file_link(self, identifier: Union[str, UUID]) -> FileLink:
        """Generate the FileLink object referenced by the passed argument."""
        if isinstance(identifier, FileLink):
            return identifier
        try:  # Check if the string is actually a UUID
            if isinstance(identifier, str):
                identifier = UUID(identifier)
        except ValueError:
            pass
        if isinstance(identifier, UUID):
            # Assume it's the file UUID on platform
            hit = next((f for f in self.list() if str(identifier) in f.url), None)
            if hit is None:
                raise ValueError(f"Found no file associated with UUID {identifier}")
            else:
                return hit
        elif isinstance(identifier, str) and self._is_external_url(identifier):
            # Assume it's an absolute URL
            filename = urlparse(identifier).path.split('/')[-1]
            file_dict = {
                'url': identifier,
                'filename': filename,
                'type': GEMDFileLink.typ
            }
            return FileLink.build(file_dict)
        elif isinstance(identifier, str) and self._validate_filelink_url(identifier):
            # It's an on-platform URL
            hit = next((f for f in self.list() if identifier == f.url), None)
            if hit is None:
                raise ValueError(f"Found no file with URL {identifier}")
            else:
                return hit
        elif isinstance(identifier, str):
            # Assume it's the filename on platform
            hit = next((f for f in self.list() if identifier == f.filename), None)
            if hit is None:
                raise ValueError(f"Found no file named {identifier}")
            else:
                return hit
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
    def _validate_filelink_url(url):
        """Verify link is well formed."""
        parsed = urlparse(url)
        if len(parsed.scheme) > 0 or len(parsed.netloc) > 0:
            # Absolute
            return False
        if len(parsed.query) > 0 or len(parsed.fragment) > 0:
            # Illegal modifiers
            return False

        split_path = parsed.path.split('/')
        return len(split_path) >= 4 and split_path[-4] == 'files' and split_path[-2] == 'versions'
