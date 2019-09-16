"""A collection of FileLink objects."""
from uuid import UUID
import os
import mimetypes
from boto3 import client as boto3_client
import requests
from botocore.exceptions import ClientError

from taurus.entity.file_link import FileLink as TaurusFileLink
from citrine._serialization.properties import String
from citrine._rest.collection import Collection
from citrine._rest.resource import Resource
from citrine._session import Session


class FileLink(Resource['FileLink'], TaurusFileLink):
    """Resource that stores the name and url of an external file."""

    filename = String('filename')
    url = String('url')

    def __init__(self, filename: str, url: str):
        TaurusFileLink.__init__(self, filename, url)

    def __str__(self):
        return '<File link {!r}>'.format(self.filename)

    def download(self, dest_path: str, session: Session):
        """
        Download the file associated with this file link.

        Parameters
        ----------
        dest_path: str
            foo

        Returns
        -------
        none
        """
        path = self.url + '/content-link'
        foo = session.get_resource(path)
        url = foo['pre_signed_read_link']
        params = {'s3_bucket': foo['s3_bucket'], 's3_key': foo['s3_key'],
                  's3_version': foo['s3_version']}
        requests.get(url, params=params)


class FileCollection(Collection[FileLink]):
    """Represents the collection of all file links associated with a dataset."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/files'
    _individual_key = 'file'
    _collection_key = 'files'

    def __init__(self, project_id: UUID, dataset_id: UUID, session: Session):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.session = session

    def build(self, data: dict) -> FileLink:
        """Build an instance of FileLink."""
        return FileLink.build(data)

    def upload(self, file_path, dest_name=None) -> FileLink:
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

        path = self._get_path() + "/uploads"
        extension = os.path.splitext(file_path)[1]
        mimeType = mimetypes.types_map[extension]
        upload_json = {
            'files': [
                {
                    'file_name': dest_name,
                    'mime_type': mimeType,
                    'size': os.stat(file_path).st_size
                }
            ]
        }
        # POST request creates space in S3 for the file and returns AWS-related information
        # (such as temporary credentials) that allow the file to be uploaded.
        upload_response = self.session.post_resource(path=path, json=upload_json)

        # Extract all relevant information from the POST response
        try:
            region_name = upload_response['s3_region']
            aws_access_key_id = upload_response['temporary_credentials']['access_key_id']
            aws_secret_access_key = upload_response['temporary_credentials']['secret_access_key']
            aws_session_token = upload_response['temporary_credentials']['session_token']
            bucket = upload_response['s3_bucket']
            region = upload_response["s3_region"]
            object_key = upload_response['uploads'][0]['s3_key']
            upload_id = upload_response['uploads'][0]['upload_id']
        except KeyError:
            raise RuntimeError("Upload initiation response is missing some fields: "
                               "{}".format(upload_response))

        s3_client = boto3_client('s3',
                                 region_name=region_name,
                                 aws_access_key_id=aws_access_key_id,
                                 aws_secret_access_key=aws_secret_access_key,
                                 aws_session_token=aws_session_token)
        with open(file_path, 'rb') as f:
            try:
                upload_s3_response = s3_client.put_object(
                    Bucket=bucket,
                    Key=object_key,
                    Body=f,
                    Metadata={"X-Citrine-Upload-Id": upload_id})
            except ClientError as e:
                raise RuntimeError("Upload of file {} failed with the following "
                                   "exception: {}".format(file_path, e))
            s3_version = upload_s3_response['VersionId']
            path = self._get_path() + "/uploads/{}/complete".format(upload_id)
            complete_response = self.session.put_resource(path=path, json={'s3_version': s3_version})

        try:
            file_id = complete_response['file_info']['file_id']
            version = complete_response['file_info']['version']
        except KeyError:
            raise RuntimeError("Upload completion response is missing some "
                               "fields: {}".format(complete_response))
        file_link_dict = {
            'filename': dest_name,
            'url': self._get_path(file_id) + '/versions/{}'.format(version)
        }
        return FileLink.build(file_link_dict)
