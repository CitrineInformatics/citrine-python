import json
from logging import getLogger
from typing import Union, Iterable, Optional, Any, Tuple
from uuid import uuid4
from warnings import warn

import requests

from citrine._rest.collection import Collection
from citrine._rest.paginator import Paginator
from citrine._rest.resource import Resource, ResourceTypeEnum
from citrine._serialization import properties
from citrine._serialization.properties import UUID
from citrine._session import Session
from citrine._utils.functions import rewrite_s3_links_locally, write_file_locally, \
    format_escaped_url
from citrine.jobs.job import JobSubmissionResponse, _poll_for_job_completion
from citrine.resources.table_config import TableConfig, TableConfigCollection

logger = getLogger(__name__)


class GemTable(Resource['Table']):
    """A 2-dimensional projection of data.

    GEM Tables are the basic unit used to flatten and manipulate data objects.
    While data objects can represent complex materials data, the format
    is NOT conducive to analysis and machine learning. GEM Tables, however,
    can be used to 'flatten' data objects into useful projections.
    """

    _response_key = 'table'
    _resource_type = ResourceTypeEnum.TABLE

    uid = properties.UUID('id')
    """:UUID: unique Citrine id of this GEM Table"""
    version = properties.Integer('version')
    """:int: Version number of the GEM Table.
    The first table built from a given config is version 1."""
    download_url = properties.String('signed_download_url')
    """:str: URL pointing to the location of the GEM Table's contents.
    This is an expiring download link and is not unique."""

    _config = properties.Optional(properties.Object(TableConfig), "config", serializable=False)
    _name = properties.Optional(properties.String, "name", serializable=False)
    _description = properties.Optional(properties.String, "description", serializable=False)

    def __init__(self):
        self._project_id = None
        self._session = None

    def __str__(self):
        return '<GEM Table {!r}, version {}>'.format(self.uid, self.version)

    @property
    def config(self) -> TableConfig:
        """Configuration used to build the table."""
        if self._config is None:
            config_collection = TableConfigCollection(self._project_id, self._session)
            self._config = config_collection.get_for_table(self)
        return self._config

    @property
    def name(self) -> str:
        """Name of the table (inherited from the config)."""
        if self._name is None:
            self._name = self.config.name
        return self._name

    @property
    def description(self) -> str:
        """Description of the table (inherited from the config)."""
        if self._description is None:
            self._description = self.config.description
        return self._description


class GemTableVersionPaginator(Paginator[GemTable]):
    """
    A Paginator for GEM Tables.

    For a single table, we share the same UID, but have different versions -
    ensure that (uid, version) is used for comparisons.
    """

    def _comparison_fields(self, entity: GemTable) -> Any:
        return (entity.uid, entity.version)


class GemTableCollection(Collection[GemTable]):
    """Represents the collection of all tables associated with a project."""

    _path_template = 'projects/{project_id}/display-tables'
    _collection_key: str = 'tables'
    _paginator: Paginator = GemTableVersionPaginator()
    _resource = GemTable

    def __init__(self, project_id: UUID, session: Session):
        self.project_id = project_id
        self.session: Session = session

    def get(self, uid: Union[UUID, str], *, version: Optional[int] = None) -> GemTable:
        """Get a Table's metadata. If no version is specified, get the most recent version."""
        if version is not None:
            path = self._get_path(uid) + format_escaped_url("/versions/{}", version)
            data = self.session.get_resource(path)
            return self.build(data)
        else:
            tables = self.list_versions(uid)
            newest_table = max(tables, key=lambda x: x.version or 0)
            return newest_table

    def list_versions(self,
                      uid: UUID,
                      *,
                      page: Optional[int] = None,
                      per_page: int = 100) -> Iterable[GemTable]:
        """
        List the versions of a table given a specific Table UID.

        This is a paginated collection, similar to a .list() call.


        :param uid: The Table UID.
        :param page: The page number to display (eg: 1)
        :param per_page: The number of items to fetch per-page.
        :return: An iterable of the versions of the Tables (as Table objects).
        """
        def _fetch_versions(page: Optional[int],
                            per_page: int) -> Tuple[Iterable[dict], str]:
            data = self.session.get_resource(self._get_path(uid),
                                             params=self._page_params(page, per_page))
            return data[self._collection_key], data.get('next', "")

        def _build_versions(collection: Iterable[dict]) -> Iterable[GemTable]:
            for item in collection:
                yield self.build(item)

        return self._paginator.paginate(
            # Don't deduplicate on uid since uids are shared between versions
            _fetch_versions, _build_versions, page, per_page, deduplicate=False)

    def list_by_config(self,
                       table_config_uid: UUID,
                       *,
                       page: Optional[int] = None,
                       per_page: int = 100) -> Iterable[GemTable]:
        """
        List the versions of a table associated with a given Table Config UID.

        This is a paginated collection, similar to a .list() call.


        :param table_config_uid: The Table Config UID.
        :param page: The page number to display (eg: 1)
        :param per_page: The number of items to fetch per-page.
        :return: An iterable of the versions of the Tables (as Table objects).
        """
        def _fetch_versions(page: Optional[int],
                            per_page: int) -> Tuple[Iterable[dict], str]:
            path_params = {'table_config_uid_str': str(table_config_uid)}
            path_params.update(self.__dict__)
            path = format_escaped_url(
                'projects/{project_id}/table-configs/{table_config_uid_str}/gem-tables',
                **path_params
            )
            data = self.session.get_resource(
                path,
                params=self._page_params(page, per_page))
            return data[self._collection_key], data.get('next', "")

        def _build_versions(collection: Iterable[dict]) -> Iterable[GemTable]:
            for item in collection:
                yield self.build(item)

        return self._paginator.paginate(
            # Don't deduplicate on uid since uids are shared between versions
            _fetch_versions, _build_versions, page, per_page, deduplicate=False)

    def initiate_build(self, config: Union[TableConfig, str, UUID], *,
                       version: Union[str, UUID] = None) -> JobSubmissionResponse:
        """
        [ALPHA] Initiates tables build with provided config.

        This method does not wait for job completion. If you do not need to build
        multiple tables in parallel, using build_from_config is preferable to using
        this method. Use get_by_build_job to wait for the result of this method.

        Parameters
        ----------
        config:
            The persisted table config from which to build a table (or its ID).
        version
            The version of the table config; only necessary when config is a uid.

        Returns
        -------
            Information about the submitted job. Note the format of this object
            may be unstable.

        """
        if isinstance(config, TableConfig):
            if version is not None:
                logger.warning('Ignoring version {} since config object was provided.'
                               .format(version))
            if config.version_number is None:
                raise ValueError('Cannot build table from config which has no version. '
                                 'Try registering the config before building.')
            if config.uid is None:
                raise ValueError('Cannot build table from config which has no uid. '
                                 'Try registering the config before building.')
            uid = config.uid
            version = config.version_number
        else:
            if version is None:
                raise ValueError('Version must be specified when building by config uid.')
            uid = config
        job_id = uuid4()
        logger.info('Building table from config {} version {} with job ID {}...'
                    .format(uid, version, job_id))
        path = format_escaped_url('projects/{}/ara-definitions/{}/versions/{}/build',
                                  self.project_id, uid, version
                                  )
        response = self.session.post_resource(
            path=path,
            json={},
            params={
                'job_id': job_id
            }
        )
        submission = JobSubmissionResponse.build(response)
        logger.info('Build job submitted with job ID {}.'.format(submission.job_id))
        return submission

    def get_by_build_job(self, job: Union[JobSubmissionResponse, UUID], *,
                         timeout: float = 15 * 60) -> GemTable:
        """
        [ALPHA] Gets table by build job, waiting for it to complete if necessary.

        Parameters
        ----------
        job
            The job submission object or job ID for the table build.
        timeout
            Amount of time to wait on build job (in seconds) before giving up. Defaults
            to 15 minutes. Note that this number has no effect on the build job itself,
            which can also time out server-side.

        Returns
        -------
        GemTable
            The table built by the specified job.

        """
        status = _poll_for_job_completion(self.session, self.project_id, job, timeout=timeout)

        table_id = status.output['display_table_id']
        table_version = status.output['display_table_version']
        warning_blob = status.output.get('table_warnings')
        warnings = json.loads(warning_blob) if warning_blob is not None else []
        if warnings:
            warn_lines = ['Table build completed with warnings:']
            for warning in warnings:
                limited_results = warning.get('limited_results', [])
                warn_lines.extend(limited_results)
                total_count = warning.get('total_count', 0)
                if total_count > len(limited_results):
                    warn_lines.append('and {} more similar.'
                                      .format(total_count - len(limited_results)))
            logger.warning('\n\t'.join(warn_lines))
        return self.get(table_id, version=table_version)

    def build_from_config(self, config: Union[TableConfig, str, UUID], *,
                          version: Union[str, int] = None,
                          timeout: float = 15 * 60) -> GemTable:
        """
        [ALPHA] Builds table from table config, waiting for build job to complete.

        Parameters
        ----------
        config:
            The persisted table config from which to build a table (or its ID).
        version
            The version of the table config; only necessary when config is a uid.
        timeout
            Amount of time to wait on build job (in seconds) before giving up. Defaults
            to 15 minutes. Note that this number has no effect on the build job itself,
            which can also time out server-side.

        Returns
        -------
        GemTable
            A new table built from the supplied config.

        """
        job = self.initiate_build(config, version=version)
        return self.get_by_build_job(job, timeout=timeout)

    def build(self, data: dict) -> GemTable:
        """Build an individual Table from a dictionary."""
        table = GemTable.build(data)
        table._project_id = self.project_id
        table._session = self.session
        return table

    def register(self, model: GemTable) -> GemTable:
        """Tables cannot be created at this time."""
        raise RuntimeError('Creating Tables is not supported at this time.')

    def update(self, model: GemTable) -> GemTable:
        """Tables cannot be updated."""
        raise RuntimeError(
            "Tables cannot be updated. You may want to update a table configuration and/or "
            "re-build the table, especially if new GEMD data are available."
        )

    def delete(self, uid: Union[UUID, str]):
        """Tables cannot be deleted at this time."""
        raise NotImplementedError("Tables cannot be deleted at this time.")

    table_type = Union[GemTable, UUID, str]
    obsolete_table_type = Union[table_type, Tuple[Union[str, UUID], Union[str, int]]]

    def _read_raw(self, table: table_type) -> requests.Response:
        """
        Read the Table file from S3 into local memory.

        If a Table object is not provided, retrieve it using the provided table and version ids.


        Parameters
        ----------
        table:
            The persisted table config from which to build a table (or its ID and version number).

        Returns
        -------
        requests.Response
            The server response

        """
        if not isinstance(table, GemTable):
            table = self.get(uid=table)

        data_location = table.download_url
        data_location = rewrite_s3_links_locally(data_location, self.session.s3_endpoint_url)
        return requests.get(data_location)

    def read_to_memory(self, table: table_type) -> str:
        """
        Read the Table file from S3 into local memory.

        If a Table object is not provided, retrieve it using the provided table and version ids.


        Parameters
        ----------
        table:
            The Table object to read from the S3 server

        Returns
        -------
        str
            The contents of the file from S3, which is expected to be formatted as a CSV

        """
        return self._read_raw(table).text

    def read(self, *, table: obsolete_table_type, local_path: str):
        """
        Read the Table file from S3 to your local system.

        If a Table object is not provided, retrieve it using the provided table and version ids.


        Parameters
        ----------
        table:
            The persisted table config from which to build a table (or its ID and version number).
        local_path
            The path to the local location to save the file

        """
        # NOTE: this uses the pre-signed S3 download url. If we need to download larger files,
        # we have other options available (using multi-part downloads in parallel , for example).
        if isinstance(table, (Tuple, list)):
            warn("A tuple as a means of referring to a GEM Table is deprecated.  "
                 "Please pass a GemTable object.", DeprecationWarning)
            table = self.get(uid=table[0], version=table[1])

        response = self._read_raw(table)
        write_file_locally(response.content, local_path)
