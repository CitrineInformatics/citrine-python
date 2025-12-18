"""Resources that represent both individual and collections of projects."""
from functools import partial
from typing import Optional, Dict, List, Union, Iterable, Iterator
from uuid import UUID

from citrine._rest.collection import Collection
from citrine._rest.resource import Resource, ResourceTypeEnum
from citrine._serialization import properties
from citrine._session import Session
from citrine._utils.functions import format_escaped_url
from citrine.resources.branch import BranchCollection
from citrine.resources.descriptors import DescriptorMethods
from citrine.resources.design_space import DesignSpaceCollection
from citrine.resources.design_workflow import DesignWorkflowCollection
from citrine.resources.gemtables import GemTableCollection
from citrine.resources.predictor import PredictorCollection
from citrine.resources.predictor_evaluation_execution import \
    PredictorEvaluationExecutionCollection
from citrine.resources.predictor_evaluation_workflow import \
    PredictorEvaluationWorkflowCollection
from citrine.resources.predictor_evaluation import PredictorEvaluationCollection
from citrine.resources.generative_design_execution import \
    GenerativeDesignExecutionCollection
from citrine.resources.project_member import ProjectMember
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

    """

    _response_key = 'project'
    _resource_type = ResourceTypeEnum.PROJECT

    name = properties.String('name')
    description = properties.Optional(properties.String(), 'description')
    uid = properties.Optional(properties.UUID(), 'id')
    """UUID: Unique uuid4 identifier of this project."""
    status = properties.Optional(properties.String(), 'status')
    """str: Status of the project."""
    created_at = properties.Optional(properties.Datetime(), 'created_at')
    """int: Time the project was created, in seconds since epoch."""
    archived = properties.Optional(properties.Boolean, 'archived')
    """bool: Whether the project is archived."""
    _team_id = properties.Optional(properties.UUID, "team.id", serializable=False)

    def __init__(self,
                 name: str,
                 *,
                 description: Optional[str] = None,
                 session: Optional[Session] = None,
                 team_id: Optional[UUID] = None):
        self.name: str = name
        self.description: Optional[str] = description
        self.session: Session = session
        self._team_id: Optional[UUID] = team_id

    def _post_dump(self, data: dict) -> dict:
        return {key: value for key, value in data.items() if value is not None}

    def __str__(self):
        return '<Project {!r}>'.format(self.name)

    def _path(self):
        return format_escaped_url('/projects/{project_id}', project_id=self.uid)

    @property
    def team_id(self):
        """Returns the Team's id-scoped UUID."""
        if self._team_id is None:
            self._team_id = self.get_team_id_from_project_id(
                session=self.session,
                project_id=self.uid
            )
        return self._team_id

    @team_id.setter
    def team_id(self, value: Optional[UUID]):
        self._team_id = value

    @classmethod
    def get_team_id_from_project_id(cls, session: Session, project_id: UUID):
        """Returns the UUID of the Team that owns the project with the provided project_id."""
        response = session.get_resource(path=f'projects/{project_id}', version="v3")
        return response['project']['team']['id']

    @property
    def branches(self) -> BranchCollection:
        """Return a resource representing all visible branches."""
        return BranchCollection(project_id=self.uid, session=self.session)

    @property
    def design_spaces(self) -> DesignSpaceCollection:
        """Return a resource representing all visible design spaces."""
        return DesignSpaceCollection(project_id=self.uid, session=self.session)

    @property
    def predictors(self) -> PredictorCollection:
        """Return a resource representing all visible predictors."""
        return PredictorCollection(project_id=self.uid, session=self.session)

    @property
    def descriptors(self) -> DescriptorMethods:
        """Return a resource containing a set of methods returning descriptors."""
        return DescriptorMethods(project_id=self.uid, session=self.session)

    @property
    def predictor_evaluation_workflows(self) -> PredictorEvaluationWorkflowCollection:
        """Return a collection representing all visible predictor evaluation workflows."""
        return PredictorEvaluationWorkflowCollection(project_id=self.uid, session=self.session)

    @property
    def predictor_evaluation_executions(self) -> PredictorEvaluationExecutionCollection:
        """Return a collection representing all visible predictor evaluation executions."""
        return PredictorEvaluationExecutionCollection(project_id=self.uid, session=self.session)

    @property
    def predictor_evaluations(self) -> PredictorEvaluationCollection:
        """Return a collection representing all visible predictor evaluations."""
        return PredictorEvaluationCollection(project_id=self.uid, session=self.session)

    @property
    def design_workflows(self) -> DesignWorkflowCollection:
        """Return a collection representing all visible design workflows."""
        return DesignWorkflowCollection(project_id=self.uid, session=self.session)

    @property
    def generative_design_executions(self) -> GenerativeDesignExecutionCollection:
        """Return a collection representing all visible generative design executions."""
        return GenerativeDesignExecutionCollection(project_id=self.uid, session=self.session)

    @property
    def tables(self) -> GemTableCollection:
        """Return a resource representing all visible Tables."""
        return GemTableCollection(team_id=self.team_id, project_id=self.uid, session=self.session)

    @property
    def table_configs(self) -> TableConfigCollection:
        """Return a resource representing all Table Configs in the project."""
        return TableConfigCollection(team_id=self.team_id,
                                     project_id=self.uid,
                                     session=self.session)

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
        if resource_type == ResourceTypeEnum.DATASET:
            raise ValueError("Datasets already belong to a team, so publishing is unncessary.")

        self.session.checked_post(
            f"{self._path()}/published-resources/{resource_type}/batch-publish",
            version='v3',
            json={'ids': [resource_access["id"]]})
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
        if resource_type == ResourceTypeEnum.DATASET:
            raise ValueError("Datasets belong to a team, so unpublishing is meaningless.")

        self.session.checked_post(
            f"{self._path()}/published-resources/{resource_type}/batch-un-publish",
            version='v3',
            json={'ids': [resource_access["id"]]})
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
        if resource_type == ResourceTypeEnum.DATASET:
            raise ValueError("Pulling a dataset into a project is unnecessary.")

        base_url = f'/teams/{self.team_id}{self._path()}'
        self.session.checked_post(
            f'{base_url}/outside-resources/{resource_type}/batch-pull-in',
            version='v3',
            json={'ids': [resource_access["id"]]})
        return True

    def list_members(self) -> Union[List[ProjectMember], List["TeamMember"]]:  # noqa: F821
        """
        List all of the members in the current project.

        Returns
        -------
        List[ProjectMember] | List[TeamMember]
            The members of the current project, or the members of the team
            containing the project if teams have been released.

        """
        # Preventing a cyclical import.
        from citrine.resources.team import TeamCollection

        team_collection = TeamCollection(self.session)
        parent_team = team_collection.get(self.team_id)
        return parent_team.list_members()


class ProjectCollection(Collection[Project]):
    """
    Represents the collection of all projects as well as the resources belonging to it.

    Parameters
    ----------
    session: Session, optional
        The Citrine session used to connect to the database.

    """

    @property
    def _path_template(self):
        if self.team_id is None:
            return '/projects'
        else:
            return '/teams/{team_id}/projects'
    _individual_key = 'project'
    _collection_key = 'projects'
    _resource = Project
    _api_version = 'v3'

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

    def get(self, uid: Union[UUID, str]) -> Project:
        """
        Get a particular project.

        Parameters
        ----------
        uid: UUID or str
            The uid of the project to get.

        """
        # Only the team-agnostic project get is implemented
        if self.team_id is None:
            return super().get(uid)
        else:
            return ProjectCollection(session=self.session).get(uid)

    def register(self, name: str, *, description: Optional[str] = None) -> Project:
        """
        Create and upload new project.

        Parameters
        ----------
        name: str
            Name of the project to be created.
        description: str
            Long-form description of the project to be created.

        Return
        -------
        Project
            The newly registered project.

        """
        if self.team_id is None:
            raise NotImplementedError("Cannot register a project without a team ID. "
                                      "Use team.projects.register.")

        project = Project(name, description=description)
        return super().register(project)

    def _list_base(self, *, per_page: int = 1000, archived: Optional[bool] = None):
        filters = {}
        if archived is not None:
            filters["archived"] = str(archived).lower()

        fetcher = partial(self._fetch_page, additional_params=filters, version=self._api_version)
        return self._paginator.paginate(page_fetcher=fetcher,
                                        collection_builder=self._build_collection_elements,
                                        per_page=per_page)

    def list(self, *, per_page: int = 1000) -> Iterator[Project]:
        """
        List all projects using pagination.

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
        return self._list_base(per_page=per_page)

    def list_active(self, *, per_page: int = 1000) -> Iterator[Project]:
        """
        List non-archived projects using pagination.

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
        return self._list_base(per_page=per_page, archived=False)

    def list_archived(self, *, per_page: int = 1000) -> Iterable[Project]:
        """
        List archived projects using pagination.

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
        return self._list_base(per_page=per_page, archived=True)

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
        query_params = {'userId': ""}

        json = {} if search_params is None else {'search_params': search_params}

        data = self.session.post_resource(self._get_path(action="search"),
                                          params=query_params,
                                          json=json,
                                          version=self._api_version)

        if self._collection_key is not None:
            collections = data[self._collection_key]

        return collections

    def search(self,
               *,
               search_params: Optional[dict] = None,
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

    def archive(self, uid: Union[UUID, str]) -> Response:
        """Archive a project."""
        # Only the team-agnostic project archive is implemented
        if self.team_id is None:
            path = self._get_path(uid, action="archive")
            return self.session.post_resource(path, version=self._api_version, json=None)
        else:
            return ProjectCollection(session=self.session).archive(uid)

    def restore(self, uid: Union[UUID, str]) -> Response:
        """Restore an archived project."""
        # Only the team-agnostic project restore is implemented
        if self.team_id is None:
            path = self._get_path(uid, action="restore")
            return self.session.post_resource(path, version=self._api_version, json=None)
        else:
            return ProjectCollection(session=self.session).restore(uid)

    def delete(self, uid: Union[UUID, str]) -> Response:
        """
        Delete a particular project.

        Only empty projects can be deleted.
        If the project is not empty, then the Response will contain a list of all of the project's
        resources. These must be deleted before the project can be deleted.
        """
        # Only the team-agnostic project delete is implemented
        if self.team_id is None:
            return super().delete(uid)
        else:
            return ProjectCollection(session=self.session).delete(uid)

    def update(self, model: Project) -> Project:
        """Projects cannot be updated."""
        raise NotImplementedError("Project update is not supported at this time.")
