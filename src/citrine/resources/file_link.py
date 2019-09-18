"""A collection of FileLink objects."""
from uuid import UUID
import os
import mimetypes
from typing import Iterable
from boto3 import client as boto3_client
from botocore.exceptions import ClientError

from taurus.entity.file_link import FileLink as TaurusFileLink
from citrine._serialization.properties import String
from citrine._rest.collection import Collection
from citrine._rest.resource import Resource
from citrine._session import Session


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


class FileLink(Resource['FileLink'], TaurusFileLink):
    """Resource that stores the name and url of an external file."""

    filename = String('filename')
    url = String('url')
    typ = String('type')

    def __init__(self, filename, url):
        TaurusFileLink.__init__(self, filename, url)
        self.typ = TaurusFileLink.typ

    def __str__(self):
        return '<File link {!r}>'.format(self.filename)


class FileCollection(Collection[FileLink]):
    """Represents the collection of all file links associated with a dataset."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/files'
    _dataset_agnostic_path_template = 'projects/{project_id}/files'
    _individual_key = 'file'
    _collection_key = 'files'

    def __init__(self, project_id: UUID, dataset_id: UUID, session: Session):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.session = session

    def build(self, data: dict) -> FileLink:
        """Build an instance of FileLink."""
        return FileLink.build(data)

    def list(self) -> Iterable[FileLink]:
        url = self._get_path(ignore_dataset=False)
        params = {'dataset_id': str(self.dataset_id)}
        response = self.session.get_resource(path=url)

    def upload(self, file_path: str, dest_name: str = None) -> FileLink:
        """
        Uploads a file to the dataset.

        Parameters
        ----------
        file_path: str
            The path to the file on the local computer.
        dest_name: str, optional
            The name the file will have after being uploaded. If unspecified, the local name of
            the file will be used. That is, the file at "/Users/me/diagram.pdf" will be uploaded
            with the name "diagram.pdf".

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
        Make a request to the backend to upload a file.

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
        extension = os.path.splitext(file_path)[1]
        mime_type = mimetypes.types_map[extension]
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
        except KeyError:
            raise RuntimeError("Upload initiation response is missing some fields: "
                               "{}".format(upload_request))
        return uploader

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
        s3_client = boto3_client('s3',
                                 region_name=uploader.region_name,
                                 aws_access_key_id=uploader.aws_access_key_id,
                                 aws_secret_access_key=uploader.aws_secret_access_key,
                                 aws_session_token=uploader.aws_session_token)
        with open(file_path, 'rb') as f:
            try:
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
        path = self._get_path() + "/uploads/{}/complete".format(uploader.upload_id)
        complete_response = self.session.put_resource(path=path,
                                                      json={'s3_version': uploader.s3_version})

        try:
            file_id = complete_response['file_info']['file_id']
            version = complete_response['file_info']['version']
        except KeyError:
            raise RuntimeError("Upload completion response is missing some "
                               "fields: {}".format(complete_response))

        url = self._get_path(file_id) + '/versions/{}'.format(version)
        return FileLink(filename=dest_name, url=url)
