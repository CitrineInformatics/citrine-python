from typing import Union, Iterable, Optional, Any, Tuple

import deprecation
import requests

from citrine._rest.collection import Collection
from citrine._rest.paginator import Paginator
from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine._serialization.properties import UUID
from citrine._session import Session
from citrine._utils.functions import rewrite_s3_links_locally, write_file_locally


class Table(Resource['Table']):
    """A 2-dimensional projection of data.

    (Display) Tables are the basic unit used to flatten and manipulate data objects.
    While data objects can represent complex materials data, the format
    is NOT conducive to analysis and machine learning. Tables, however,
    can be used to 'flatten' data objects into useful projections.

    Attributes
    ----------
    uid: UUID
        Unique uuid4 identifier of this project.
    version: str
        Version number of the Table
    download_url: int
        Url pointing to the location of the Table's contents

    """

    _response_key = 'table'

    uid = properties.Optional(properties.UUID(), 'id')
    version = properties.Optional(properties.Integer, 'version')
    download_url = properties.Optional(properties.String, 'signed_download_url')

    def __init__(self):
        self.uid = None
        self.version = None
        self.download_url = None

    def __str__(self):
        # TODO: Change this to name once that's added to the table model
        return '<Table {!r}, version {}>'.format(self.uid, self.version)

    @deprecation.deprecated(deprecated_in="0.16.0", details="Use TableCollection.read() instead")
    def read(self, local_path):
        """[DEPRECATED] Use TableCollection.read() instead."""  # noqa: D402
        data_location = self.download_url
        data_location = rewrite_s3_links_locally(data_location)
        response = requests.get(data_location)
        write_file_locally(response.content, local_path)


class TableVersionPaginator(Paginator[Table]):
    """
    A Paginator for Tables.

    For a single table, we share the same UID, but have different versions -
    ensure that (uid, version) is used for comparisons.
    """

    def _comparison_fields(self, entity: Table) -> Any:
        return (entity.uid, entity.version)


class TableCollection(Collection[Table]):
    """Represents the collection of all tables associated with a project."""

    _path_template = 'projects/{project_id}/display-tables'
    _collection_key: str = 'tables'
    _paginator: Paginator = TableVersionPaginator()

    def __init__(self, project_id: UUID, session: Session):
        self.project_id = project_id
        self.session: Session = session

    def get(self, uid: Union[UUID, str], version: int) -> Table:
        """Get a Table's metadata."""
        path = self._get_path(uid) + "/versions/{}".format(version)
        data = self.session.get_resource(path)
        return self.build(data)

    def list_versions(self,
                      uid: UUID,
                      page: Optional[int] = None,
                      per_page: int = 100) -> Iterable[Table]:
        """
        List the versions of a table given a specific Table UID.

        This is a paginated collection, similar to a .list() call.


        :param uid: The Table UID.
        :param page: The page number to display (eg: 1)
        :param per_page: The number of items to fetch per-page.
        :return: An iterable of the versions of the Tables (as Table objects).
        """
        def fetch_versions(page: Optional[int],
                           per_page: int) -> Tuple[Iterable[dict], str]:
            data = self.session.get_resource(self._get_path() + '/' + str(uid),
                                             params=self._page_params(page, per_page))
            return (data[self._collection_key], data.get('next', ""))

        def build_versions(collection: Iterable[dict]) -> Iterable[Table]:
            for item in collection:
                yield self.build(item)

        return self._paginator.paginate(fetch_versions, build_versions, page, per_page)

    def build(self, data: dict) -> Table:
        """Build an individual Table from a dictionary."""
        table = Table.build(data)
        table.project_id = self.project_id
        table.session = self.session
        return table

    def register(self, model: Table) -> Table:
        """Tables cannot be created at this time."""
        raise RuntimeError('Creating Tables is not supported at this time.')

    def read(self, table: Union[Table, Tuple[str, int]], local_path: str):
        """
        Read the Table file from S3.

        If a Table object is not provided, retrieve it using the provided table and version ids.
        """
        # NOTE: this uses the pre-signed S3 download url. If we need to download larger files,
        # we have other options available (using multi-part downloads in parallel , for example).
        if isinstance(table, Tuple):
            table = self.get(table[0], table[1])

        data_location = table.download_url
        data_location = rewrite_s3_links_locally(data_location, self.session.s3_endpoint_url)
        response = requests.get(data_location)
        write_file_locally(response.content, local_path)
