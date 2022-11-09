import csv
import json
from functools import partial
from io import StringIO
from typing import Dict, Iterator, Optional, Union
from uuid import UUID

from citrine._rest.collection import Collection
from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine._session import Session
from citrine.informatics.experiment_values import ExperimentValue


class CandidateExperimentSnapshot(Serializable['CandidateExperimentSnapshot']):
    """The contents of a candidate experiment within an experiment data source."""

    uid = properties.UUID('experiment_id', serializable=False)
    """:UUID: unique Citrine id of this experiment"""
    candidate_id = properties.UUID('candidate_id', serializable=False)
    """:UUID: unique Citrine id of the candidate associated with this experiment"""
    workflow_id = properties.UUID('workflow_id', serializable=False)
    """:UUID: unique Citrine id of the design workflow which produced the associated candidate"""
    name = properties.String('name', serializable=False)
    """:str: name of the experiment"""
    description = properties.Optional(properties.String, 'description', serializable=False)
    """:Optional[str]: description of the experiment"""
    updated_time = properties.Datetime('updated_time', serializable=False)
    """:datetime: date and time at which the experiment was updated"""

    overrides = properties.Mapping(properties.String, properties.Object(ExperimentValue),
                                   'overrides')
    """:dict[str, ExperimentValue]: dictionary of candidate material variable overrides"""

    def __init__(self, *args, **kwargs):
        """Candidate experiment snapshots are not directly instantiated by the user."""
        pass  # pragma: no cover

    def _overrides_json(self) -> Dict[str, str]:
        return {name: json.dumps(expt_value.value) for name, expt_value in self.overrides.items()}


class ExperimentDataSource(Serializable['ExperimentDataSource']):
    """An experiment data source."""

    uid = properties.UUID('id', serializable=False)
    """:UUID: unique Citrine id of this experiment data source"""
    experiments = properties.List(properties.Object(CandidateExperimentSnapshot),
                                  'data.experiments',
                                  serializable=False)
    """:list[CandidateExperimentSnapshot]: list of experiment data in this data source"""
    branch_root_id = properties.UUID('metadata.branch_root_id', serializable=False)
    """:UUID: unique Citrine id of the branch root this data source is associated with"""
    version = properties.Integer('metadata.version', serializable=False)
    """:int: version of this data source"""
    created_by = properties.UUID('metadata.created.user', serializable=False)
    """:UUID: id of the user who created this data source"""
    create_time = properties.Datetime('metadata.created.time', serializable=False)
    """:datetime: date and time at which this data source was created"""

    def __init__(self, *args, **kwargs):
        """Experiment data sources are not directly instantiated by the user."""
        pass  # pragma: no cover

    def read(self) -> str:
        """Read this experiment data source into a CSV.

        Each row will be a single experiement from this data source, and each column is a variable
        which is overriden in any of the experiements in this data source. If an experiement did
        not override a variable, its cell will be left empty.

        All cells can be deserialized as JSON. Most of them will simply be strings or numbers. But
        if present,the "Formulation" cell will contain an escaped JSON string, which will
        deserialize into a mapping from ingredient names to floating-point values.
        """
        overrides = [experiment._overrides_json() for experiment in self.experiments]
        columns = {key for override in overrides for key in override.keys()}
        sorted_columns = sorted(list(columns), key=str.lower)

        buffer = StringIO()
        writer = csv.DictWriter(buffer, sorted_columns)
        writer.writeheader()
        writer.writerows(overrides)

        return buffer.getvalue()


class ExperimentDataSourceCollection(Collection[ExperimentDataSource]):
    """Represents the collection of all experiment data sources associated with a project."""

    _path_template = 'projects/{project_id}/candidate-experiment-datasources'
    _individual_key = None
    _resource = ExperimentDataSource
    _collection_key = 'response'

    def __init__(self, project_id: UUID, session: Session):
        self.project_id = project_id
        self.session: Session = session

    def build(self, data: dict) -> ExperimentDataSource:
        """Build an individual experiment result from a dictionary."""
        result = ExperimentDataSource.build(data)
        result._project_id = self.project_id
        result._session = self.session
        return result

    def list(self, *,
             per_page: int = 100,
             branch_id: Optional[UUID] = None,
             version: Optional[Union[int, str]] = None) -> Iterator[ExperimentDataSource]:
        """Paginate over the experiment data sources.

        Parameters
        ---------
        per_page: int, optional
            Max number of results to return per page. Default is 100.  This parameter
            is used when making requests to the backend service.  If the page parameter
            is specified it limits the maximum number of elements in the response.
        branch_id: UUID, optional
            Filter the list by the root branch ID.
        version: Union[int, str], optional
            Filter the list by the data source version. Also accepts "latest".

        Returns
        -------
        Iterator[ExperimentDataSource]
            An iterator that can be used to loop over all matching experiment data sources.

        """
        params = {}
        if branch_id:
            params["branch"] = branch_id
        if version:
            params["version"] = version

        fetcher = partial(self._fetch_page, additional_params=params)
        return self._paginator.paginate(page_fetcher=fetcher,
                                        collection_builder=self._build_collection_elements,
                                        per_page=per_page)

    def read(self, datasource: Union[ExperimentDataSource, UUID, str]):
        """Reads the provided experiment data source into a CSV.

        If a UUID or str is provided, it's first retrieved from the platform.

        For details on the CSV format, see
        :py:meth:`citrine.resources.experiment_datasource.ExperimentDataSource.read`.
        """
        if not isinstance(datasource, ExperimentDataSource):
            datasource = self.get(uid=datasource)

        return datasource.read()
