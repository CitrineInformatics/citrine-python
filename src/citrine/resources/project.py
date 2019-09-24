"""Resources that represent both individual and collections of projects."""
from typing import Optional, Dict

from citrine._session import Session
from citrine.resources.dataset import DatasetCollection
from citrine.resources.condition_template import ConditionTemplateCollection
from citrine.resources.parameter_template import ParameterTemplateCollection
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
    def datasets(self) -> DatasetCollection:
        """Return a resource representing all visible datasets."""
        return DatasetCollection(self.uid, self.session)

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

    def __init__(self, session: Session = Session()):
        self.session = session

    def build(self, data) -> Project:
        """
        Build an individual project from a dictionary.

        Parameters
        ----------
        data: dict
            A dictionary representing the project.

        Returns
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

    def delete(self, uuid):
        """Delete the project with the provided uid."""
        raise NotImplementedError("Delete is not supported for projects")
