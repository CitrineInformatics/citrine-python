"""Resources that represent both individual and collections of projects."""
from typing import Optional, Dict, List, Union, Iterable, Tuple
from uuid import UUID

from citrine._session import Session
from citrine.resources.ara_definition import AraDefinitionCollection
from citrine.resources.descriptors import DescriptorMethods
from citrine.resources.module import ModuleCollection
from citrine.resources.design_space import DesignSpaceCollection
from citrine.resources.processor import ProcessorCollection
from citrine.resources.predictor import PredictorCollection
from citrine.resources.response import Response
from citrine.resources.workflow import WorkflowCollection
from citrine.resources.dataset import DatasetCollection
from citrine.resources.condition_template import ConditionTemplateCollection
from citrine.resources.parameter_template import ParameterTemplateCollection
from citrine.resources.project_member import ProjectMember
from citrine.resources.project_roles import MEMBER, ROLES, ACTIONS
from citrine.resources.property_template import PropertyTemplateCollection
from citrine.resources.material_template import MaterialTemplateCollection
from citrine.resources.measurement_template import MeasurementTemplateCollection
from citrine.resources.process_template import ProcessTemplateCollection
from citrine.resources.process_run import ProcessRunCollection
from citrine.resources.process_spec import ProcessSpecCollection
from citrine.resources.measurement_run import MeasurementRunCollection
from citrine.resources.measurement_spec import MeasurementSpecCollection
from citrine.resources.material_run import MaterialRunCollection
from citrine.resources.material_spec import MaterialSpecCollection
from citrine.resources.ingredient_run import IngredientRunCollection
from citrine.resources.ingredient_spec import IngredientSpecCollection

from citrine._rest.collection import Collection
from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine.resources.table import TableCollection
from citrine.resources.user import User


class Project(Resource['Project']):
    """
    A Citrine Project.

    A project is a collection of datasets, some of which belong directly to the project
    and some of which have been shared with the project.

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

    name = properties.String('name')
    description = properties.Optional(properties.String(), 'description')
    uid = properties.Optional(properties.UUID(), 'id')
    status = properties.Optional(properties.String(), 'status')
    created_at = properties.Optional(properties.Datetime(), 'created_at')

    def __init__(self,
                 name: str,
                 description: Optional[str] = None,
                 session: Optional[Session] = Session()):
        self.name: str = name
        self.description: Optional[str] = description
        self.session: Session = session

    def __str__(self):
        return '<Project {!r}>'.format(self.name)

    def _path(self):
        return '/projects/{project_id}'.format(**{"project_id": self.uid})

    @property
    def modules(self) -> ModuleCollection:
        """Return a resource representing all visible design spaces."""
        return ModuleCollection(self.uid, self.session)

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
        """[ALPHA] Return a resource containing a set of methods returning descriptors."""
        return DescriptorMethods(self.uid, self.session)

    @property
    def workflows(self) -> WorkflowCollection:
        """Return a resource representing all visible workflows."""
        return WorkflowCollection(self.uid, self.session)

    @property
    def datasets(self) -> DatasetCollection:
        """Return a resource representing all visible datasets."""
        return DatasetCollection(self.uid, self.session)

    @property
    def tables(self) -> TableCollection:
        """Return a resource representing all visible Tables."""
        return TableCollection(self.uid, self.session)

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
    def ara_definitions(self) -> AraDefinitionCollection:
        """Return a resource representing all ara definitions in the project."""
        return AraDefinitionCollection(self.uid, self.session)

    def share(self,
              project_id: str,
              resource_type: str,
              resource_id: str) -> Dict[str, str]:
        """Share a resource with another project."""
        return self.session.post_resource(self._path() + "/share", {
            "project_id": project_id,
            "resource": {"type": resource_type, "id": resource_id}
        })

    def make_public(self,
                    resource: Resource) -> bool:
        """
        Grant public access to a resource owned by this project.

        Parameters
        ----------
        resource: Resource
            An instance of a resource owned by this project (e.g. a dataset).

        Returns
        -------
        bool
            True if the action was performed successfully

        """
        self.session.checked_post(self._path() + "/make-public", {
            "resource": resource.as_entity_dict()
        })
        return True

    def make_private(self,
                     resource: Resource) -> bool:
        """
        Remove public access for a resource owned by this project.

        Parameters
        ----------
        resource: Resource
            An instance of a resource owned by this project (e.g. a dataset).

        Returns
        -------
        bool
            True if the action was performed successfully

        """
        self.session.checked_post(self._path() + "/make-private", {
            "resource": resource.as_entity_dict()
        })
        return True

    def list_members(self) -> List[ProjectMember]:
        """
        List all of the members in the current project.

        Returns
        -------
        List[ProjectMember]
            The members of the current project

        """
        members = self.session.get_resource(self._path() + "/users")["users"]
        return [ProjectMember(user=User.build(m), project=self, role=m["role"]) for m in members]

    def update_user_role(self, user_uid: Union[str, UUID], role: ROLES, actions: ACTIONS = []):
        """
        Update a User's role and action permissions in the Project.

        Valid roles are MEMBER or LEAD.

        WRITE is the only action available for specification.

        Returns
        -------
        bool
            Returns True if user role successfully updated

        """
        self.session.checked_post(self._path() + "/users/{}".format(user_uid),
                                  {'role': role, 'actions': actions})
        return True

    def add_user(self, user_uid: Union[str, UUID]):
        """
        Add a User to a Project.

        Adds User with MEMBER role to the Project.
        Use the update_user_rule method to change a User's role.

        Returns
        -------
        bool
            Returns True if user successfully added

        """
        self.session.checked_post(self._path() + "/users/{}".format(user_uid),
                                  {'role': MEMBER, 'actions': []})
        return True

    def remove_user(self, user_uid: Union[str, UUID]) -> bool:
        """
        Remove a User from a Project.

        Returns
        -------
        bool
            Returns True if user successfully removed

        """
        self.session.checked_delete(
            self._path() + "/users/{}".format(user_uid)
        )
        return True


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

    def __init__(self, session: Session = Session()):
        self.session = session

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
        return project

    def register(self, name: str, description: Optional[str] = None) -> Project:
        """
        Create and upload new project.

        Parameters
        ----------
        name: str
            Name of the project to be created.
        description: str
            Long-form description of the project to be created.

        """
        return super().register(Project(name, description))

    def search(self, search_params: Optional[dict] = None,
               per_page: int = 100) -> Iterable[Project]:
        """
        Search for projects matching the desired name or description.

        You can search for projects matching the desired name or description by either exact match
        or substring match, as specified by the search_params argument. Defaults to no search
        criteria.

        Like list, this method allows for pagination. This differs from the list function, because
        it makes a POST request to resourceType/search with search fields in a post body.

        Leaving page and per_page as default values will yield all elements in the collection,
        paginating over all available pages.

        Leaving search_params as its default value will return mimic the behavior of a full list
        with no search parameters.

        Parameters
        ---------
        search_params: dict, optional
            A dict representing the body of the post request that will be sent to the search
            endpoint to filter the results ie.
            {
                "search_params": {
                    "name": {
                        "value": "Polymer Project",
                        "search_method": "EXACT"
                    },
                    "description": {
                        "value": "polymer chain length",
                        "search_method": "SUBSTRING"
                    },
                }
            }
            The dict can constain any combination of (one or all) search specifications for the
            name, description, and status fields of a project. For each parameter specified, the
            "value" to match, as well as the "search_method" must be provided. The available
            search_methods are "SUBSTRING" and "EXACT". The example above demonstrates the input
            necessary to list projects with the exact name "Polymer Project," and descriptions
            including the phrase "polymer chain length,"

        per_page: int, optional
            Max number of results to return per page. Default is 100.  This parameter is used when
            making requests to the backend service.  If the page parameter is specified it limits
            the maximum number of elements in the response.

        Returns
        -------
        Iterable[Project]
            Projects in this collection.

        """
        # To avoid setting default to {} -> reduce mutation risk, and to make more extensible
        search_params = {} if search_params is None else search_params

        return self._paginator.paginate(page_fetcher=self._fetch_page_search,
                                        collection_builder=self._build_collection_elements,
                                        per_page=per_page,
                                        search_params=search_params)

    def delete(self, uid: Union[UUID, str]) -> Response:
        """[ALPHA] Delete a particular element of the collection."""
        return super().delete(uid)  # pragma: no cover

    def _fetch_page_search(self, page: Optional[int] = None,
                           per_page: Optional[int] = None,
                           search_params: Optional[dict] = None) -> Tuple[Iterable[dict], str]:
        """
        Fetch resources that match the supplied search parameters.

        Fetches resources that match the supplied search_params, by calling _fetch_page with
        checked_post, the path to the POST resource-type/search endpoint, any pagination
        parameters, and the request body to the search endpoint.

        Parameters
        ---------
        page: int, optional
            The "page" of results to list. Default is the first page, which is 1.
        per_page: int, optional
            Max number of results to return. Default is 20.
        search_params: dict, optional
            A dict representing a request body that could be sent to a POST request. The "json"
            field should be passed as the key for the outermost dict, with its value the request
            body, so that we can easily unpack the keyword argument when it gets passed to
            fetch_func.
            ie. { 'search_params': {'name': {'value': 'Project', 'search_method': 'SUBSTRING'} } }

        Returns
        -------
        Iterable[dict]
            Elements in this collection.
        str
            The next uri if one is available, empty string otherwise

        """
        # Making 'json' the key of the outermost dict, so that search_params can be passed
        # directly to the function making the request with keyword expansion
        json_body = {} if search_params is None else {'json': search_params}

        path = self._get_path() + "/search"

        return self._fetch_page(path=path, fetch_func=self.session.post_resource,
                                page=page, per_page=per_page,
                                json_body=json_body)
