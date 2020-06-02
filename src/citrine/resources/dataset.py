"""Resources that represent both individual and collections of datasets."""
from collections import defaultdict
from typing import TypeVar, List
from uuid import UUID

from citrine._rest.collection import Collection
from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine._session import Session
from citrine._utils.functions import scrub_none
from citrine.resources.condition_template import ConditionTemplateCollection
from citrine.resources.file_link import FileCollection
from citrine.resources.ingredient_run import IngredientRunCollection
from citrine.resources.ingredient_spec import IngredientSpecCollection
from citrine.resources.material_run import MaterialRunCollection
from citrine.resources.material_spec import MaterialSpecCollection
from citrine.resources.material_template import MaterialTemplateCollection
from citrine.resources.measurement_run import MeasurementRunCollection
from citrine.resources.measurement_spec import MeasurementSpecCollection
from citrine.resources.measurement_template import MeasurementTemplateCollection
from citrine.resources.parameter_template import ParameterTemplateCollection
from citrine.resources.process_run import ProcessRunCollection
from citrine.resources.process_spec import ProcessSpecCollection
from citrine.resources.process_template import ProcessTemplateCollection
from citrine.resources.property_template import PropertyTemplateCollection
from gemd.entity.object import MeasurementSpec, MeasurementRun, MaterialSpec, MaterialRun, \
    ProcessSpec, ProcessRun, IngredientSpec, IngredientRun
from gemd.entity.template.condition_template import ConditionTemplate
from gemd.entity.template.material_template import MaterialTemplate
from gemd.entity.template.measurement_template import MeasurementTemplate
from gemd.entity.template.parameter_template import ParameterTemplate
from gemd.entity.template.process_template import ProcessTemplate
from gemd.entity.template.property_template import PropertyTemplate
from gemd.entity.base_entity import BaseEntity
from gemd.util import writable_sort_order

ResourceType = TypeVar('ResourceType', bound='DataConcepts')


class Dataset(Resource['Dataset']):
    """
    A collection of data objects.

    Datasets are the basic unit of access control. A user with read access to a dataset can view
    every object in that dataset. A user with write access to a dataset can create, update,
    and delete objects in the dataset.

    Parameters
    ----------
    name: str
        Name of the dataset. Can be used for searching.
    summary: str
        A summary of this dataset.
    description: str
        Long-form description of the dataset.

    Attributes
    ----------
    uid: UUID
        Unique uuid4 identifier of this dataset.
    deleted: bool
        Flag indicating whether or not this dataset has been deleted.
    created_by: UUID
        ID of the user who created the dataset.
    updated_by: UUID
        ID of the user who last updated the dataset.
    deleted_by: UUID
        ID of the user who deleted the dataset, if it is deleted.
    create_time: int
        Time the dataset was created, in seconds since epoch.
    update_time: int
        Time the dataset was most recently updated, in seconds since epoch.
    delete_time: int
        Time the dataset was deleted, in seconds since epoch, if it is deleted.
    public: bool
        Flag indicating whether the dataset is publicly readable.

    """

    _response_key = 'dataset'

    uid = properties.Optional(properties.UUID(), 'id')
    name = properties.String('name')
    summary = properties.String('summary')
    description = properties.String('description')
    deleted = properties.Optional(properties.Boolean(), 'deleted')
    created_by = properties.Optional(properties.UUID(), 'created_by')
    updated_by = properties.Optional(properties.UUID(), 'updated_by')
    deleted_by = properties.Optional(properties.UUID(), 'deleted_by')
    create_time = properties.Optional(properties.Datetime(), 'create_time')
    update_time = properties.Optional(properties.Datetime(), 'update_time')
    delete_time = properties.Optional(properties.Datetime(), 'delete_time')
    public = properties.Optional(properties.Boolean(), 'public')

    def __init__(self, name: str, summary: str, description: str):
        self.name: str = name
        self.summary: str = summary
        self.description: str = description

        # The attributes below should not be set by the user. Instead they will be updated as the
        # dataset interacts with the backend data service
        self.uid = None
        self.deleted = None
        self.created_by = None
        self.updated_by = None
        self.deleted_by = None
        self.create_time = None
        self.update_time = None
        self.delete_time = None
        self.public = None

    def __str__(self):
        return '<Dataset {!r}>'.format(self.name)

    @property
    def property_templates(self) -> PropertyTemplateCollection:
        """Return a resource representing all property templates in this dataset."""
        return PropertyTemplateCollection(self.project_id, self.uid, self.session)

    @property
    def condition_templates(self) -> ConditionTemplateCollection:
        """Return a resource representing all condition templates in this dataset."""
        return ConditionTemplateCollection(self.project_id, self.uid, self.session)

    @property
    def parameter_templates(self) -> ParameterTemplateCollection:
        """Return a resource representing all parameter templates in this dataset."""
        return ParameterTemplateCollection(self.project_id, self.uid, self.session)

    @property
    def material_templates(self) -> MaterialTemplateCollection:
        """Return a resource representing all material templates in this dataset."""
        return MaterialTemplateCollection(self.project_id, self.uid, self.session)

    @property
    def measurement_templates(self) -> MeasurementTemplateCollection:
        """Return a resource representing all measurement templates in this dataset."""
        return MeasurementTemplateCollection(self.project_id, self.uid, self.session)

    @property
    def process_templates(self) -> ProcessTemplateCollection:
        """Return a resource representing all process templates in this dataset."""
        return ProcessTemplateCollection(self.project_id, self.uid, self.session)

    @property
    def process_runs(self) -> ProcessRunCollection:
        """Return a resource representing all process runs in this dataset."""
        return ProcessRunCollection(self.project_id, self.uid, self.session)

    @property
    def measurement_runs(self) -> MeasurementRunCollection:
        """Return a resource representing all measurement runs in this dataset."""
        return MeasurementRunCollection(self.project_id, self.uid, self.session)

    @property
    def material_runs(self) -> MaterialRunCollection:
        """Return a resource representing all material runs in this dataset."""
        return MaterialRunCollection(self.project_id, self.uid, self.session)

    @property
    def ingredient_runs(self) -> IngredientRunCollection:
        """Return a resource representing all ingredient runs in this dataset."""
        return IngredientRunCollection(self.project_id, self.uid, self.session)

    @property
    def process_specs(self) -> ProcessSpecCollection:
        """Return a resource representing all process specs in this dataset."""
        return ProcessSpecCollection(self.project_id, self.uid, self.session)

    @property
    def measurement_specs(self) -> MeasurementSpecCollection:
        """Return a resource representing all measurement specs in this dataset."""
        return MeasurementSpecCollection(self.project_id, self.uid, self.session)

    @property
    def material_specs(self) -> MaterialSpecCollection:
        """Return a resource representing all material specs in this dataset."""
        return MaterialSpecCollection(self.project_id, self.uid, self.session)

    @property
    def ingredient_specs(self) -> IngredientSpecCollection:
        """Return a resource representing all ingredient specs in this dataset."""
        return IngredientSpecCollection(self.project_id, self.uid, self.session)

    @property
    def files(self) -> FileCollection:
        """Return a resource representing all files in the dataset."""
        return FileCollection(self.project_id, self.uid, self.session)

    def _collection_for(self, data_concepts_resource):
        if isinstance(data_concepts_resource, MeasurementTemplate):
            return self.measurement_templates
        if isinstance(data_concepts_resource, MeasurementSpec):
            return self.measurement_specs
        if isinstance(data_concepts_resource, MeasurementRun):
            return self.measurement_runs

        if isinstance(data_concepts_resource, MaterialTemplate):
            return self.material_templates
        if isinstance(data_concepts_resource, MaterialSpec):
            return self.material_specs
        if isinstance(data_concepts_resource, MaterialRun):
            return self.material_runs

        if isinstance(data_concepts_resource, ProcessTemplate):
            return self.process_templates
        if isinstance(data_concepts_resource, ProcessSpec):
            return self.process_specs
        if isinstance(data_concepts_resource, ProcessRun):
            return self.process_runs

        if isinstance(data_concepts_resource, IngredientSpec):
            return self.ingredient_specs
        if isinstance(data_concepts_resource, IngredientRun):
            return self.ingredient_runs

        if isinstance(data_concepts_resource, PropertyTemplate):
            return self.property_templates
        if isinstance(data_concepts_resource, ParameterTemplate):
            return self.parameter_templates
        if isinstance(data_concepts_resource, ConditionTemplate):
            return self.condition_templates

    def register(self, data_concepts_resource: ResourceType, dry_run=False) -> ResourceType:
        """Register a data concepts resource to the appropriate collection."""
        return self._collection_for(data_concepts_resource)\
            .register(data_concepts_resource, dry_run=dry_run)

    def register_all(self, data_concepts_resources: List[ResourceType],
                     dry_run=False) -> List[ResourceType]:
        """
        Register multiple data concepts resources to each of their appropriate collections.

        Does so in an order that is guaranteed to store all linked items before the item that
        references them.

        The uids of the input data concepts resources are updated with their on-platform uids.
        This supports storing an object that has a reference to an object that doesn't have a uid.

        Parameters
        ----------
        data_concepts_resources: List[ResourceType]
            The resources to register. Can be different types.

        dry_run: bool
            Whether to actually register the item or run a dry run of the register operation.
            Dry run is intended to be used for validation. Default: false

        Returns
        -------
        List[ResourceType]
            The registered versions

        """
        resources = list()
        by_type = defaultdict(list)
        for obj in data_concepts_resources:
            by_type[obj.typ].append(obj)
        typ_groups = sorted(list(by_type.values()), key=lambda x: writable_sort_order(x[0]))
        batch_size = 50
        for typ_group in typ_groups:
            num_batches = len(typ_group) // batch_size
            for batch_num in range(num_batches + 1):
                batch = typ_group[batch_num * batch_size: (batch_num + 1) * batch_size]
                if batch:  # final batch is empty when batch_size divides len(typ_group)
                    registered = self._collection_for(batch[0])\
                        .register_all(batch, dry_run=dry_run)
                    for prewrite, postwrite in zip(batch, registered):
                        if isinstance(postwrite, BaseEntity):
                            prewrite.uids = postwrite.uids
                    resources.extend(registered)
        return resources


class DatasetCollection(Collection[Dataset]):
    """
    Represents the collection of all datasets associated with a project.

    Parameters
    ----------
    project_id: UUID
        Unique ID of the project this dataset collection belongs to.
    session: Session
        The Citrine session used to connect to the database.

    """

    _path_template = 'projects/{project_id}/datasets'
    _individual_key = None
    _collection_key = None

    def __init__(self, project_id: UUID, session: Session):
        self.project_id = project_id
        self.session: Session = session

    def build(self, data: dict) -> Dataset:
        """
        Build an individual dataset from a dictionary.

        Parameters
        ----------
        data: dict
            A dictionary representing the dataset.

        Returns
        -------
        Dataset
            The dataset created from data.

        """
        dataset = Dataset.build(data)
        dataset.project_id = self.project_id
        dataset.session = self.session
        return dataset

    def register(self, model: Dataset) -> Dataset:
        """
        Create a new element of the collection by registering an existing resource.

        This differs from super().register() in that None fields are scrubbed, and the json
        response is not assumed to come in a dictionary with a single entry 'dataset'.
        Both of these behaviors are in contrast to the behavior of projects. Eventually they
        will be unified in the backend, and one register() method will suffice.

        Parameters
        ----------
        model: Dataset
            The dataset to register.

        Returns
        -------
        Dataset
            A copy of the registered dataset as it now exists in the database.

        """
        path = self._get_path()
        dumped_dataset = model.dump()
        dumped_dataset["deleted"] = None
        data = self.session.post_resource(path, scrub_none(dumped_dataset))
        full_model = self.build(data)
        full_model.project_id = self.project_id
        return full_model
