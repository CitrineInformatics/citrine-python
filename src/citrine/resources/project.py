"""Resources that represent both individual and collections of projects."""
from functools import partial
from typing import Optional, Dict, List, Union, Iterable, Tuple, Iterator
from uuid import UUID

from gemd.entity.base_entity import BaseEntity
from gemd.entity.link_by_uid import LinkByUID

from citrine._rest.collection import Collection
from citrine._rest.resource import Resource, ResourceTypeEnum
from citrine._serialization import properties
from citrine._session import Session
from citrine._utils.functions import format_escaped_url
from citrine.exceptions import NonRetryableException, ModuleRegistrationFailedException
from citrine.resources.api_error import ApiError
from citrine.resources.branch import BranchCollection
from citrine.resources.condition_template import ConditionTemplateCollection
from citrine.resources.dataset import DatasetCollection
from citrine.resources.delete import _async_gemd_batch_delete
from citrine.resources.descriptors import DescriptorMethods
from citrine.resources.design_space import DesignSpaceCollection
from citrine.resources.design_workflow import DesignWorkflowCollection
from citrine.resources.gemd_resource import GEMDResourceCollection
from citrine.resources.gemtables import GemTableCollection
from citrine.resources.ingredient_run import IngredientRunCollection
from citrine.resources.ingredient_spec import IngredientSpecCollection
from citrine.resources.material_run import MaterialRunCollection
from citrine.resources.material_spec import MaterialSpecCollection
from citrine.resources.material_template import MaterialTemplateCollection
from citrine.resources.measurement_run import MeasurementRunCollection
from citrine.resources.measurement_spec import MeasurementSpecCollection
from citrine.resources.measurement_template import MeasurementTemplateCollection
from citrine.resources.module import ModuleCollection
from citrine.resources.parameter_template import ParameterTemplateCollection
from citrine.resources.predictor import PredictorCollection
from citrine.resources.predictor_evaluation_execution import \
    PredictorEvaluationExecutionCollection
from citrine.resources.predictor_evaluation_workflow import \
    PredictorEvaluationWorkflowCollection
from citrine.resources.generative_design_execution import \
    GenerativeDesignExecutionCollection
from citrine.resources.process_run import ProcessRunCollection
from citrine.resources.process_spec import ProcessSpecCollection
from citrine.resources.process_template import ProcessTemplateCollection
from citrine.resources.project_member import ProjectMember
from citrine.resources.property_template import PropertyTemplateCollection
from citrine.resources.response import Response
from citrine.resources.table_config import TableConfigCollection


class Project(Resource['Project']):
    """
    A Citrine Project.

    A project is a collection of datasets and AI assets, some of which belong directly
    to the project, and some of which have been shared with the project.

    Parameters
    ----------
    name: str
        Name of the project.
    description: str
        Long-form description of the project.
    session: Session, optional
        The Citrine session used to connect to the database.

    Attributes
    ----------
    uid: UUID
        Unique uuid4 identifier of this project.
    status: str
        Status of the project.
    created_at: int
        Time the project was created, in seconds since epoch.

    """

    _response_key = 'project'
    _resource_type = ResourceTypeEnum.PROJECT

    name = properties.String('name')
    description = properties.Optional(properties.String(), 'description')
    uid = properties.Optional(properties.UUID(), 'id')
    status = properties.Optional(properties.String(), 'status')
    created_at = properties.Optional(properties.Datetime(), 'created_at')
    team_id = properties.Optional(properties.UUID, "team.id", serializable=False)

    def __init__(self,
                 name: str,
                 *,
                 description: Optional[str] = None,
                 session: Optional[Session] = None,
                 team_id: Optional[UUID] = None):
        self.name: str = name
        self.description: Optional[str] = description
        self.session: Session = session
        self.team_id: Optional[UUID] = team_id

    def _post_dump(self, data: dict) -> dict:
        return {key: value for key, value in data.items() if value is not None}

    def __str__(self):
        return '<Project {!r}>'.format(self.name)

    def _path(self):
        return format_escaped_url('/projects/{project_id}', project_id=self.uid)

    @property
    def modules(self) -> ModuleCollection:
        """Return a resource representing all visible design spaces."""
        return ModuleCollection(self.uid, self.session)

    @property
    def branches(self) -> BranchCollection:
        """Return a resource representing all visible branches."""
        return BranchCollection(self.uid, self.session)

    @property
    def design_spaces(self) -> DesignSpaceCollection:
        """Return a resource representing all visible design spaces."""
        return DesignSpaceCollection(self.uid, self.session)

    @property
    def predictors(self) -> PredictorCollection:
        """Return a resource representing all visible predictors."""
        return PredictorCollection(self.uid, self.session)

    @property
    def descriptors(self) -> DescriptorMethods:
        """Return a resource containing a set of methods returning descriptors."""
        return DescriptorMethods(self.uid, self.session)

    @property
    def predictor_evaluation_workflows(self) -> PredictorEvaluationWorkflowCollection:
        """Return a collection representing all visible predictor evaluation workflows."""
        return PredictorEvaluationWorkflowCollection(self.uid, self.session)

    @property
    def predictor_evaluation_executions(self) -> PredictorEvaluationExecutionCollection:
        """Return a collection representing all visible predictor evaluation executions."""
        return PredictorEvaluationExecutionCollection(project_id=self.uid, session=self.session)

    @property
    def design_workflows(self) -> DesignWorkflowCollection:
        """Return a collection representing all visible design workflows."""
        return DesignWorkflowCollection(project_id=self.uid, session=self.session)

    @property
    def generative_design_executions(self) -> GenerativeDesignExecutionCollection:
        """Return a collection representing all visible generative design executions."""
        return GenerativeDesignExecutionCollection(project_id=self.uid, session=self.session)

    @property
    def datasets(self) -> DatasetCollection:
        """Return a resource representing all visible datasets."""
        return DatasetCollection(self.uid, self.session)

    @property
    def tables(self) -> GemTableCollection:
        """Return a resource representing all visible Tables."""
        return GemTableCollection(self.uid, self.session)

    @property
    def property_templates(self) -> PropertyTemplateCollection:
        """Return a resource representing all property templates in this dataset."""
        return PropertyTemplateCollection(self.uid, None, self.session)

    @property
    def condition_templates(self) -> ConditionTemplateCollection:
        """Return a resource representing all condition templates in this dataset."""
        return ConditionTemplateCollection(self.uid, None, self.session)

    @property
    def parameter_templates(self) -> ParameterTemplateCollection:
        """Return a resource representing all parameter templates in this dataset."""
        return ParameterTemplateCollection(self.uid, None, self.session)

    @property
    def material_templates(self) -> MaterialTemplateCollection:
        """Return a resource representing all material templates in this dataset."""
        return MaterialTemplateCollection(self.uid, None, self.session)

    @property
    def measurement_templates(self) -> MeasurementTemplateCollection:
        """Return a resource representing all measurement templates in this dataset."""
        return MeasurementTemplateCollection(self.uid, None, self.session)

    @property
    def process_templates(self) -> ProcessTemplateCollection:
        """Return a resource representing all process templates in this dataset."""
        return ProcessTemplateCollection(self.uid, None, self.session)

    @property
    def process_runs(self) -> ProcessRunCollection:
        """Return a resource representing all process runs in this dataset."""
        return ProcessRunCollection(self.uid, None, self.session)

    @property
    def measurement_runs(self) -> MeasurementRunCollection:
        """Return a resource representing all measurement runs in this dataset."""
        return MeasurementRunCollection(self.uid, None, self.session)

    @property
    def material_runs(self) -> MaterialRunCollection:
        """Return a resource representing all material runs in this dataset."""
        return MaterialRunCollection(self.uid, None, self.session)

    @property
    def ingredient_runs(self) -> IngredientRunCollection:
        """Return a resource representing all ingredient runs in this dataset."""
        return IngredientRunCollection(self.uid, None, self.session)

    @property
    def process_specs(self) -> ProcessSpecCollection:
        """Return a resource representing all process specs in this dataset."""
        return ProcessSpecCollection(self.uid, None, self.session)

    @property
    def measurement_specs(self) -> MeasurementSpecCollection:
        """Return a resource representing all measurement specs in this dataset."""
        return MeasurementSpecCollection(self.uid, None, self.session)

    @property
    def material_specs(self) -> MaterialSpecCollection:
        """Return a resource representing all material specs in this dataset."""
        return MaterialSpecCollection(self.uid, None, self.session)

    @property
    def ingredient_specs(self) -> IngredientSpecCollection:
        """Return a resource representing all ingredient specs in this dataset."""
        return IngredientSpecCollection(self.uid, None, self.session)

    @property
    def gemd(self) -> GEMDResourceCollection:
        """Return a resource representing all GEMD objects/templates in this dataset."""
        return GEMDResourceCollection(self.uid, None, self.session)

    @property
    def table_configs(self) -> TableConfigCollection:
        """Return a resource representing all Table Configs in the project."""
        return TableConfigCollection(self.uid, self.session)

    def publish(self, *, resource: Resource):
        """
        Publish a resource from a project to its encompassing team.

        In order to use the Resource in a different project,
        you should use project.pull_in_resource() to pull that resource
        into the other project.

        Parameters
        ----------
        resource: Resource
            The resource owned by this project, which will be published

        Returns
        -------
        bool
            Returns ``True`` if resource successfully published

        """
        resource_access = resource.access_control_dict()
        resource_type = resource_access["type"]
        self.session.checked_post(
            f"{self._path()}/published-resources/{resource_type}/batch-publish",
            version='v3', json={'ids': [resource_access["id"]]})
        return True

    def un_publish(self, *, resource: Resource):
        """
        Un-publish a resource from a project from its encompassing team.

        Parameters
        ----------
        resource: Resource
            The resource owned by this project, which will be un-published

        Returns
        -------
        bool
            Returns ``True`` if resource successfully un-published

        """
        resource_access = resource.access_control_dict()
        resource_type = resource_access["type"]
        self.session.checked_post(
            f"{self._path()}/published-resources/{resource_type}/batch-un-publish",
            version='v3', json={'ids': [resource_access["id"]]})
        return True

    def pull_in_resource(self, *, resource: Resource):
        """
        Pull in a public resource from this project's team.

        Parameters
        ----------
        resource: Resource
            The resource owned by the encompassing team, which will be pulled in

        Returns
        -------
        bool
            Returns ``True`` if resource successfully pulled in

        """
        resource_access = resource.access_control_dict()
        resource_type = resource_access["type"]
        base_url = f'/teams/{self.team_id}{self._path()}'
        self.session.checked_post(
            f'{base_url}/outside-resources/{resource_type}/batch-pull-in',
            version='v3', json={'ids': [resource_access["id"]]})
        return True

    def owned_dataset_ids(self) -> List[str]:
        """
        List all the ids of the datasets owned by the current project.

        Returns
        -------
        List[str]
            The ids of the modules owned by current project

        """
        query_params = {"userId": "", "domain": self._path(), "action": "WRITE"}
        return self.session.get_resource("/DATASET/authorized-ids",
                                         params=query_params,
                                         version="v3")['ids']

    def list_members(self) -> Union[List[ProjectMember], List["TeamMember"]]:  # noqa: F821
        """
        List all of the members in the current project.

        Returns
        -------
        List[ProjectMember] | List[TeamMember]
            The members of the current project, or the members of the team
            containing the project if teams have been released.

        """
        from citrine.resources.team import TeamCollection

        team_collection = TeamCollection(self.session)
        parent_team = team_collection.get(self.team_id)
        return parent_team.list_members()

    def gemd_batch_delete(
            self,
            id_list: List[Union[LinkByUID, UUID, str, BaseEntity]],
            *,
            timeout: float = 2 * 60,
            polling_delay: float = 1.0
    ) -> List[Tuple[LinkByUID, ApiError]]:
        """
        Remove a set of GEMD objects.

        You may provide GEMD objects that reference each other, and the objects
        will be removed in the appropriate order.

        A failure will be returned if the object cannot be deleted due to an external
        reference.

        You must have Write access on the associated datasets for each object.

        Parameters
        ----------
        id_list: List[Union[LinkByUID, UUID, str, BaseEntity]]
            A list of the IDs of data objects to be removed. They can be passed
            as a LinkByUID tuple, a UUID, a string, or the object itself. A UUID
            or string is assumed to be a Citrine ID, whereas a LinkByUID or
            BaseEntity can also be used to provide an external ID.
        timeout: float
            Amount of time to wait on the job (in seconds) before giving up. Defaults
            to 2 minutes. Note that this number has no effect on the underlying job
            itself, which can also time out server-side.
        polling_delay: float
            How long to delay between each polling retry attempt (in seconds).

        Returns
        -------
        List[Tuple[LinkByUID, ApiError]]
            A list of (LinkByUID, api_error) for each failure to delete an object.
            Note that this method doesn't raise an exception if an object fails to be
            deleted.

        """
        return _async_gemd_batch_delete(id_list, self.uid, self.session, None,
                                        timeout=timeout, polling_delay=polling_delay)


class ProjectCollection(Collection[Project]):
    """
    Represents the collection of all projects as well as the resources belonging to it.

    Parameters
    ----------
    session: Session, optional
        The Citrine session used to connect to the database.

    """

    _path_template = '/projects'
    _individual_key = 'project'
    _collection_key = 'projects'
    _resource = Project

    @property
    def _api_version(self):
        return 'v3'

    def __init__(self, session: Session, *, team_id: Optional[UUID] = None):
        self.session = session
        self.team_id = team_id

    def build(self, data) -> Project:
        """
        Build an individual project from a dictionary.

        Parameters
        ----------
        data: dict
            A dictionary representing the project.

        Return
        -------
        Project
            The project created from data.

        """
        project = Project.build(data)
        project.session = self.session
        if self.team_id is not None:
            project.team_id = self.team_id
        return project

    def register(self, name: str, *, description: Optional[str] = None):
        """
        Create and upload new project.

        Parameters
        ----------
        name: str
            Name of the project to be created.
        description: str
            Long-form description of the project to be created.

        """
        if self.team_id is None:
            raise NotImplementedError("Cannot register a project without a team ID. "
                                      "Use team.projects.register.")

        path = format_escaped_url('teams/{team_id}/projects', team_id=self.team_id)
        project = Project(name, description=description)
        try:
            data = self.session.post_resource(path, project.dump(), version=self._api_version)
            data = data[self._individual_key]
            return self.build(data)
        except NonRetryableException as e:
            raise ModuleRegistrationFailedException(project.__class__.__name__, e)

    def list(self, *, per_page: int = 1000) -> Iterator[Project]:
        """
        List projects using pagination.

        Parameters
        ---------
        per_page: int, optional
            Max number of results to return per page. Default is 1000.  This parameter
            is used when making requests to the backend service.  If the page parameter
            is specified it limits the maximum number of elements in the response.

        Returns
        -------
        Iterator[Project]
            Projects in this collection.

        """
        if self.team_id is None:
            path = '/projects'
        else:
            path = format_escaped_url('/teams/{team_id}/projects', team_id=self.team_id)

        fetcher = partial(self._fetch_page, path=path)
        return self._paginator.paginate(page_fetcher=fetcher,
                                        collection_builder=self._build_collection_elements,
                                        per_page=per_page)

    def search_all(self, search_params: Optional[Dict]) -> Iterable[Dict]:
        """
        Search across all projects in a domain.

        There is no pagination on search_all.

         This is compatible with accounts v3 only.

        Parameters
        ----------
        search_params: dict, optional
            A ``dict`` representing the body of the post request that will be sent to the search
            endpoint to filter the results, e.g.,

            .. code:: python

                {
                    "name": {
                        "value": "Polymer Project",
                        "search_method": "EXACT"
                    },
                    "description": {
                        "value": "polymer chain length",
                        "search_method": "SUBSTRING"
                    },
                }

            The ``dict`` can contain any combination of (one or all) search specifications for the
            name, description, and status fields of a project. For each parameter specified, the
            ``"value"`` to match, as well as the ``"search_method"`` must be provided.
            The available ``search_methods`` are ``"SUBSTRING"`` and ``"EXACT"``. The example above
            demonstrates the input necessary to list projects with the exact name
            ``"Polymer Project"`` and descriptions including the phrase ``"polymer chain length"``.


        Returns
        -------
        Iterable[Dict]
            Projects in this collection.

        """
        collections = []
        path = self._get_path() + '/search'
        query_params = {'userId': ""}

        json = {} if search_params is None else {'search_params': search_params}

        data = self.session.post_resource(path,
                                          params=query_params,
                                          json=json,
                                          version=self._api_version)

        if self._collection_key is not None:
            collections = data[self._collection_key]

        return collections

    def search(self, *, search_params: Optional[dict] = None,
               per_page: int = 1000) -> Iterable[Project]:
        """
        Search for projects matching the desired name or description.

        You can search for projects matching the desired name or description by either exact match
        or substring match, as specified by the search_params argument. Defaults to no search
        criteria.

        Like ``list``, this method allows for pagination. This differs from the list function,
        because it makes a POST request to resourceType/search with search fields in a post body.

        Leaving page and per_page as default values will yield all elements in the collection,
        paginating over all available pages.

        Leaving ``search_params`` as its default value will return mimic the behavior of
        a full list with no search parameters.

        Parameters
        ----------
        search_params: dict, optional
            A ``dict`` representing the body of the post request that will be sent to the search
            endpoint to filter the results, e.g.,

            .. code:: python

                {
                    "name": {
                        "value": "Polymer Project",
                        "search_method": "EXACT"
                    },
                    "description": {
                        "value": "polymer chain length",
                        "search_method": "SUBSTRING"
                    },
                }

            The ``dict`` can contain any combination of (one or all) search specifications for the
            name, description, and status fields of a project. For each parameter specified, the
            ``"value"`` to match, as well as the ``"search_method"`` must be provided.
            The available ``search_methods`` are ``"SUBSTRING"`` and ``"EXACT"``. The example above
            demonstrates the input necessary to list projects with the exact name
            ``"Polymer Project"`` and descriptions including the phrase ``"polymer chain length"``.

        per_page: int, optional
            Max number of results to return per page. Default is 100.  This parameter is used when
            making requests to the backend service.  If the page parameter is specified it limits
            the maximum number of elements in the response.

        Returns
        -------
        Iterable[Project]
            Projects in this collection.

        """
        return self._build_collection_elements(self.search_all(search_params))
        # To avoid setting default to {} -> reduce mutation risk, and to make more extensible

    def delete(self, uid: Union[UUID, str]) -> Response:
        """
        Delete a particular project.

        Only empty projects can be deleted.
        If the project is not empty, then the Response will contain a list of all of the project's
        resources. These must be deleted before the project can be deleted.
        """
        return super().delete(uid)

    def update(self, model: Project) -> Project:
        """Projects cannot be updated."""
        raise NotImplementedError("Project update is not supported at this time.")
