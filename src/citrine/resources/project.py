"""Resources that represent both individual and collections of projects."""
from functools import partial
from typing import Optional, Dict, List, Union, Iterable, Tuple, Iterator
from uuid import UUID
from warnings import warn

from gemd.entity.base_entity import BaseEntity
from gemd.entity.link_by_uid import LinkByUID

from citrine._rest.collection import Collection
from citrine._rest.resource import Resource, ResourceTypeEnum
from citrine._serialization import properties
from citrine._session import Session
from citrine._utils.functions import format_escaped_url, use_teams
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
from citrine.resources.process_run import ProcessRunCollection
from citrine.resources.process_spec import ProcessSpecCollection
from citrine.resources.process_template import ProcessTemplateCollection
from citrine.resources.processor import ProcessorCollection
from citrine.resources.project_member import ProjectMember
from citrine.resources.project_roles import MEMBER, ROLES, ACTIONS
from citrine.resources.property_template import PropertyTemplateCollection
from citrine.resources.response import Response
from citrine.resources.table_config import TableConfigCollection
from citrine.resources.user import User


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
    def processors(self) -> ProcessorCollection:
        """Return a resource representing all visible processors."""
        return ProcessorCollection(self.uid, self.session)

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

    @use_teams("project.make_public", True)
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

    @use_teams("project.make_private", True)
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

    @use_teams("project.make_public", True)
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

    @use_teams("project.publish")
    def share(self, *,
              resource: Optional[Resource] = None,
              project_id: Optional[Union[str, UUID]] = None,
              resource_type: Optional[str] = None,
              resource_id: Optional[str] = None
              ) -> Dict[str, str]:
        """Share a resource with another project.

        Parameters
        ----------
        resource: Resource
            The resource owned by this project, which will be shared
        project_id: Union[str, UUID]
            The id of the project with which to share the resource
        resource_type: Optional[str]
            [DEPRECATED] Please use ``resource`` instead
            The type of the resource to share. Must be one of DATASET, MODULE, USER,
            TABLE, OR TABLE_DEFINITION
        resource_id: Optional[str]
            [DEPRECATED] Please use ``resource`` instead
            The id of the resource to share

        """
        resource_dict = None
        if resource is not None:
            resource_dict = resource.access_control_dict()
        if resource_type is not None and resource_id is not None:
            warn("Asset sharing through resource_type and resource_id is deprecated. Please pass "
                 "the resource to share instead.", DeprecationWarning)
            if resource_dict is not None:
                raise ValueError("Cannot specify resource to share and also specify the "
                                 "resource type and id")
            resource_dict = {"type": resource_type, "id": resource_id}
        if resource_dict is None:
            raise ValueError("Must specify resource to share or specify the resource type and id")
        return self.session.post_resource(f"{self._path()}/share", {
            "project_id": str(project_id),
            "resource": resource_dict
        })

    @use_teams("project.publish")
    def transfer_resource(self, *, resource: Resource,
                          receiving_project_uid: Union[str, UUID]) -> bool:
        """
        Transfer ownership of a resource.

        The new owner of the the supplied resource becomes the project
        with ``uid == receiving_project_uid``.

        Parameters
        ----------
        resource: Resource
            The resource owned by this project, which will get transferred to
            the project with ``uid == receiving_project_uid``.
        receiving_project_uid: Union[string, UUID]
            The uid of the project to which the resource will be transferred.

        Returns
        -------
        bool
            Returns ``True`` upon successful resource transfer.

        """
        try:
            self.session.checked_post(f"{self._path()}/transfer-resource", {
                "to_project_id": str(receiving_project_uid),
                "resource": resource.access_control_dict()})
        except AttributeError:  # If _resource_type is not implemented
            raise RuntimeError(f"Resource of type  {resource.__class__.__name__} "
                               f"cannot be made transferred")

        return True

    @use_teams("project.publish")
    def make_public(self, resource: Resource) -> bool:
        """
        Grant public access to a resource owned by this project.

        Parameters
        ----------
        resource: Resource
            An instance of a resource owned by this project (e.g., a dataset).

        Returns
        -------
        bool
            ``True`` if the action was performed successfully

        """
        try:
            self.session.checked_post(f"{self._path()}/make-public", {
                "resource": resource.access_control_dict()
            })
        except AttributeError:  # If _resource_type is not implemented
            raise RuntimeError(f"Resource of type  {resource.__class__.__name__} "
                               f"cannot be made public")
        return True

    @use_teams("project.un_publish")
    def make_private(self, resource: Resource) -> bool:
        """
        Remove public access for a resource owned by this project.

        Parameters
        ----------
        resource: Resource
            An instance of a resource owned by this project (e.g., a dataset).

        Returns
        -------
        bool
            ``True`` if the action was performed successfully

        """
        try:
            self.session.checked_post(f"{self._path()}/make-private", {
                "resource": resource.access_control_dict()
            })
        except AttributeError:  # If _resource_type is not implemented
            raise RuntimeError(f"Resource of type  {resource.__class__.__name__} "
                               f"cannot be made private")
        return True

    def creator(self) -> str:
        """
        Return the creator of this project.

        Returns
        -------
        str
            The email of the creator of this resource.

        """
        if self.session._accounts_service_v3:
            raise NotImplementedError("Not available")
        email = self.session.get_resource(f"{self._path()}/creator")["email"]
        return email

    def owned_dataset_ids(self) -> List[str]:
        """
        List all the ids of the datasets owned by the current project.

        Returns
        -------
        List[str]
            The ids of the modules owned by current project

        """
        if self.session._accounts_service_v3:
            query_params = {"userId": "", "domain": self._path(), "action": "WRITE"}
            dataset_ids = self.session.get_resource("/DATASET/authorized-ids",
                                                    params=query_params,
                                                    version="v3")['ids']
        else:
            dataset_ids = self.session.get_resource(f"{self._path()}/dataset_ids")["dataset_ids"]
        return dataset_ids

    def owned_table_ids(self) -> List[str]:
        """
        List all the ids of the tables owned by the current project.

        Returns
        -------
        List[str]
            The ids of the tables owned by current project

        """
        if self.session._accounts_service_v3:
            raise NotImplementedError("Not available")
        table_ids = self.session.get_resource(f"{self._path()}/table_ids")["table_ids"]
        return table_ids

    def owned_table_config_ids(self) -> List[str]:
        """
        List all the ids of the table configs owned by the current project.

        Returns
        -------
        List[str]
            The ids of the table configs owned by current project

        """
        if self.session._accounts_service_v3:
            raise NotImplementedError("Not available")
        result = self.session.get_resource(f"{self._path()}/table_definition_ids")
        return result["table_definition_ids"]

    @use_teams("team.list_members")
    def list_members(self) -> List[ProjectMember]:
        """
        List all of the members in the current project.

        Returns
        -------
        List[ProjectMember]
            The members of the current project

        """
        members = self.session.get_resource(f"{self._path()}/users")["users"]
        return [ProjectMember(user=User.build(m), project=self, role=m["role"]) for m in members]

    @use_teams("team.update_user_action")
    def update_user_role(self, *, user_uid: Union[str, UUID], role: ROLES, actions: ACTIONS = []):
        """
        Update a User's role and action permissions in the Project.

        Valid roles are ``MEMBER`` or ``LEAD``.

        ``WRITE`` is the only action available for specification.

        Returns
        -------
        bool
            Returns ``True`` if user role successfully updated

        """
        self.session.checked_post(self._path() + format_escaped_url("/users/{}", user_uid),
                                  {'role': role, 'actions': actions})
        return True

    @use_teams("team.add_user")
    def add_user(self, user_uid: Union[str, UUID]):
        """
        Add a User to a Project.

        Adds User with ``MEMBER`` role to the Project.
        Use the ``update_user_rule`` method to change a User's role.

        Returns
        -------
        bool
            Returns ``True`` if user successfully added

        """
        self.session.checked_post(self._path() + format_escaped_url("/users/{}", user_uid),
                                  {'role': MEMBER, 'actions': []})
        return True

    @use_teams("team.remove_user")
    def remove_user(self, user_uid: Union[str, UUID]) -> bool:
        """
        Remove a User from a Project.

        Returns
        -------
        bool
            Returns ``True`` if user successfully removed

        """
        self.session.checked_delete(
            self._path() + format_escaped_url("/users/{}", user_uid)
        )
        return True

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
        return 'v3' if self.session._accounts_service_v3 else 'v1'

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

    def _register_in_team(self, name: str, *, description: Optional[str] = None):
        if self.team_id is None:
            raise NotImplementedError("Please use team.projects")
        path = format_escaped_url('teams/{team_id}/projects', team_id=self.team_id)
        project = Project(name, description=description)
        try:
            data = self.session.post_resource(path, project.dump(), version=self._api_version)
            data = data[self._individual_key]
            return self.build(data)
        except NonRetryableException as e:
            raise ModuleRegistrationFailedException(project.__class__.__name__, e)

    def register(self, name: str, *, description: Optional[str] = None) -> Project:
        """
        Create and upload new project.

        Parameters
        ----------
        name: str
            Name of the project to be created.
        description: str
            Long-form description of the project to be created.

        """
        if self.session._accounts_service_v3:
            return self._register_in_team(name, description=description)
        else:
            return super().register(Project(name, description=description))

    def list(self, *,
             page: Optional[int] = None,
             per_page: int = 1000) -> Iterator[Project]:
        """
        List projects using pagination.

        Leaving page and per_page as default values will yield all elements in the
        collection, paginating over all available pages.

        Parameters
        ---------
        page: int, optional
            The "page" of results to list. Default is to read all pages and yield
            all results.  This option is deprecated.
        per_page: int, optional
            Max number of results to return per page. Default is 1000.  This parameter
            is used when making requests to the backend service.  If the page parameter
            is specified it limits the maximum number of elements in the response.

        Returns
        -------
        Iterator[Project]
            Projects in this collection.

        """
        if self.session._accounts_service_v3:
            return self._list_v3(page=page, per_page=per_page)
        else:
            return super().list(page=page, per_page=per_page)

    def _list_v3(self, *, page: Optional[int] = None, per_page: int = 1000) -> Iterator[Project]:
        if self.team_id is None:
            raise NotImplementedError("Please use team.projects")

        path = format_escaped_url('/teams/{team_id}/projects', team_id=self.team_id)

        fetcher = partial(self._fetch_page, path=path)
        return self._paginator.paginate(page_fetcher=fetcher,
                                        collection_builder=self._build_collection_elements,
                                        page=page,
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
        if self.session._accounts_service_v3:
            return self._build_collection_elements(self.search_all(search_params))
        # To avoid setting default to {} -> reduce mutation risk, and to make more extensible

        return self._paginator.paginate(page_fetcher=self._fetch_page_search,
                                        collection_builder=self._build_collection_elements,
                                        per_page=per_page,
                                        search_params=search_params)

    def delete(self, uid: Union[UUID, str]) -> Response:
        """
        [ALPHA] Delete a particular project.

        Only empty projects can be deleted.
        If the project is not empty, then the Response will contain a list of all of the project's
        resources. These must be deleted before the project can be deleted.
        """
        return super().delete(uid)

    def update(self, model: Project) -> Project:
        """Projects cannot be updated."""
        raise NotImplementedError("Project update is not supported at this time.")

    def _fetch_page_search(self, page: Optional[int] = None,
                           per_page: Optional[int] = None,
                           search_params: Optional[dict] = None) -> Tuple[Iterable[dict], str]:
        """
        Fetch resources that match the supplied search parameters.

        Fetches resources that match the supplied ``search_params``, by calling ``_fetch_page``
        with ``checked_post``, the path to the POST resource-type/search endpoint, any pagination
        parameters, and the request body to the search endpoint.

        Parameters
        ---------
        page: int, optional
            The "page" of results to list. Default is the first page, which is 1.
        per_page: int, optional
            Max number of results to return. Default is 20.
        search_params: dict, optional
            A ``dict`` representing a request body that could be sent to a POST request. The "json"
            field should be passed as the key for the outermost ``dict``, with its value the
            request body, so that we can easily unpack the keyword argument when it gets passed to
            ``fetch_func``, e.g., ``{'name': {'value': 'Project', 'search_method': 'SUBSTRING'} }``

        Returns
        -------
        Iterable[dict]
            Elements in this collection.
        str
            The next uri if one is available, empty string otherwise

        """
        # Making 'json' the key of the outermost dict, so that search_params can be passed
        # directly to the function making the request with keyword expansion
        json_body = {} if search_params is None else {'json': {'search_params': search_params}}

        path = self._get_path() + "/search"

        return self._fetch_page(path=path, fetch_func=self.session.post_resource,
                                page=page, per_page=per_page,
                                json_body=json_body)
