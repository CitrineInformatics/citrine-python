"""A collection of FileLink objects."""
from uuid import UUID
import os
import mimetypes

from taurus.entity.file_link import FileLink as TaurusFileLink
from citrine._rest.collection import Collection
from citrine._rest.resource import Resource
from citrine._session import Session


class FileLink(Resource['FileLink'], TaurusFileLink):
    pass


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
        return FileLink.build(data)

    def upload(self, file_path, dest_name=None):
        """
        Uploads a file to the dataset.

        Parameters
        ----------
        file_path: str
            The path to the file on the local computer.
        dest_name: str, optional
            The name the file will have after being uploaded. If unspecifiied, the local name of
            the file will be used. That is, the file at "/Users/me/diagram.pdf" will be uploaded
            with the name "diagram.pdf".

        """
        if not os.path.isfile(file_path):
            raise ValueError("No file at specified path {}".format(file_path))

        if not dest_name:
            dest_name = os.path.basename(file_path)

        path = self._get_path() + "/uploads"
        extension = os.path.splitext(file_path)[1]
        mimeType = mimetypes.types_map[extension]
        upload_json = {
            'filename': dest_name,
            'metadata': dict(),
            'mimeType': mimeType,
            'size': str(os.stat(file_path).st_size)
        }
        self.session.post_resource(path=path, json=upload_json)
