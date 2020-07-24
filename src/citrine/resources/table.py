import json
from logging import getLogger
from time import time, sleep
from typing import Union, Iterable, Optional, Any, Tuple
from uuid import uuid4

import deprecation
import requests

from citrine._rest.collection import Collection
from citrine._rest.paginator import Paginator
from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine._serialization.properties import UUID
from citrine._session import Session
from citrine._utils.functions import rewrite_s3_links_locally, write_file_locally
from citrine.resources.ara_definition import AraDefinition
from citrine.resources.ara_job import JobSubmissionResponse, JobStatusResponse

logger = getLogger(__name__)


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
    _resource = Table

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

    def list_by_config(self,
                       ara_definition_uid: UUID,
                       page: Optional[int] = None,
                       per_page: int = 100) -> Iterable[Table]:
        """
        List the versions of a table associated with a given Table Config UID.

        This is a paginated collection, similar to a .list() call.


        :param uid: The Table Config UID.
        :param page: The page number to display (eg: 1)
        :param per_page: The number of items to fetch per-page.
        :return: An iterable of the versions of the Tables (as Table objects).
        """
        def fetch_versions(page: Optional[int],
                           per_page: int) -> Tuple[Iterable[dict], str]:
            path_params = {'ara_definition_uid_str': str(ara_definition_uid)}
            path_params.update(self.__dict__)
            path = 'projects/{project_id}/table-configs/{ara_definition_uid_str}/gem-tables'\
                .format(**path_params)
            data = self.session.get_resource(
                path,
                params=self._page_params(page, per_page))
            return data[self._collection_key], data.get('next', "")

        def build_versions(collection: Iterable[dict]) -> Iterable[Table]:
            for item in collection:
                yield self.build(item)

        return self._paginator.paginate(fetch_versions, build_versions, page, per_page)

    def initiate_build(self, config: Union[AraDefinition, str, UUID],
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
            The version of the table config, only necessary when config is a uid.

        Returns
        -------
            Information about the submitted job. Note the format of this object
            may be unstable.

        """
        if isinstance(config, AraDefinition):
            if version is not None:
                logger.warning('Ignoring version {} since config object was provided.'
                               .format(version))
            if config.version_number is None:
                raise ValueError('Cannot build table from config which has no version. '
                                 'Try registering the config before building.')
            if config.definition_uid is None:
                raise ValueError('Cannot build table from config which has no uid. '
                                 'Try registering the config before building.')
            uid = config.definition_uid
            version = config.version_number
        else:
            if version is None:
                raise ValueError('Version must be specified when building by config uid.')
            uid = config
        job_id = uuid4()
        logger.info('Building table from config {} version {} with job ID {}...'
                    .format(uid, version, job_id))
        path = 'projects/{}/ara-definitions/{}/versions/{}/build'.format(
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
                         timeout: float = 15 * 60) -> Table:
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
        Table
            The table built by the specified job.

        """
        if isinstance(job, JobSubmissionResponse):
            job_id = job.job_id
        else:
            job_id = job  # pragma: no cover
        path = 'projects/{}/execution/job-status'.format(self.project_id)
        params = {'job_id': job_id}
        start_time = time()
        while True:
            response = self.session.get_resource(path=path, params=params)
            status: JobStatusResponse = JobStatusResponse.build(response)
            if status.status in ['Success', 'Failure']:
                break
            elif time() - start_time < timeout:
                logger.info('Build job still in progress, polling status again in 2 seconds.')
                sleep(2)
            else:
                logger.error('Build job exceeded user timeout of {} seconds.'.format(timeout))
                logger.debug('Last status: {}'.format(status.dump()))
                raise TimeoutError('Build job {} timed out.'.format(job_id))
        if status.status == 'Failure':
            logger.debug('Job terminated with Failure status: {}'.format(status.dump()))
            for task in status.tasks:
                if task.status == 'Failure':
                    logger.error('Task {} failed with reason "{}"'.format(
                        task.id, task.failure_reason))
            raise RuntimeError('Job {} terminated with Failure status.'.format(job_id))
        else:
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
            return self.get(table_id, table_version)

    def build_from_config(self, config: Union[AraDefinition, str, UUID], *,
                          version: Union[str, int] = None,
                          timeout: float = 15 * 60) -> Table:
        """
        [ALPHA] Builds table from table config, waiting for build job to complete.

        Parameters
        ----------
        config:
            The persisted table config from which to build a table (or its ID).
        version
            The version of the table config, only necessary when config is a uid.
        timeout
            Amount of time to wait on build job (in seconds) before giving up. Defaults
            to 15 minutes. Note that this number has no effect on the build job itself,
            which can also time out server-side.

        Returns
        -------
        Table
            A new table built from the supplied config.

        """
        job = self.initiate_build(config, version)
        return self.get_by_build_job(job, timeout=timeout)

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
