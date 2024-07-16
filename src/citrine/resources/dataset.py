"""Resources that represent both individual and collections of datasets."""
from typing import List, Optional, Union, Tuple, Iterator, Iterable
from uuid import UUID

from gemd.entity.base_entity import BaseEntity
from gemd.entity.link_by_uid import LinkByUID

from citrine._utils.functions import format_escaped_url, _pad_positional_args
from citrine._rest.collection import Collection
from citrine._rest.resource import Resource, ResourceTypeEnum
from citrine._serialization import properties
from citrine._session import Session
from citrine._utils.functions import scrub_none, _data_manager_deprecation_checks
from citrine.exceptions import NotFound
from citrine.resources.api_error import ApiError
from citrine.resources.condition_template import ConditionTemplateCollection
from citrine.resources.data_concepts import DataConcepts
from citrine.resources.delete import _poll_for_async_batch_delete_result
from citrine.resources.file_link import FileCollection
from citrine.resources.ingestion import IngestionCollection
from citrine.resources.gemd_resource import GEMDResourceCollection
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
    summary: Optional[str]
        An optional summary of this dataset.
    description: Optional[str]
        An optional long-form description of the dataset.
    unique_name: Optional[str]
        An optional, globally unique name that can be used to retrieve the dataset.

    """

    _response_key = 'dataset'
    _resource_type = ResourceTypeEnum.DATASET

    uid = properties.Optional(properties.UUID(), 'id')
    """UUID: Unique uuid4 identifier of this dataset."""
    name = properties.String('name')
    unique_name = properties.Optional(properties.String(), 'unique_name')
    summary = properties.Optional(properties.String, 'summary')
    description = properties.Optional(properties.String, 'description')
    deleted = properties.Optional(properties.Boolean(), 'deleted')
    """bool: Flag indicating whether or not this dataset has been deleted."""
    created_by = properties.Optional(properties.UUID(), 'created_by')
    """UUID: ID of the user who created the dataset."""
    updated_by = properties.Optional(properties.UUID(), 'updated_by')
    """UUID: ID of the user who last updated the dataset."""
    deleted_by = properties.Optional(properties.UUID(), 'deleted_by')
    """UUID: ID of the user who deleted the dataset, if it is deleted."""
    create_time = properties.Optional(properties.Datetime(), 'create_time')
    """int: Time the dataset was created, in seconds since epoch."""
    update_time = properties.Optional(properties.Datetime(), 'update_time')
    """int: Time the dataset was most recently updated, in seconds since epoch."""
    delete_time = properties.Optional(properties.Datetime(), 'delete_time')
    """int: Time the dataset was deleted, in seconds since epoch, if it is deleted."""
    public = properties.Optional(properties.Boolean(), 'public')
    """bool: Flag indicating whether the dataset is publicly readable."""
    project_id = properties.Optional(properties.UUID(), 'project_id',
                                     serializable=False, deserializable=False)
    """project_id will be needed here until deprecation is complete.
    This class property will be removed post deprecation"""
    team_id = properties.Optional(properties.UUID(), 'team_id',
                                  serializable=False, deserializable=False)
    session = properties.Optional(properties.Object(Session), 'session',
                                  serializable=False, deserializable=False)

    def __init__(self, name: str, *, summary: Optional[str] = None,
                 description: Optional[str] = None, unique_name: Optional[str] = None):
        self.name: str = name
        self.summary: Optional[str] = summary
        self.description: Optional[str] = description
        self.unique_name = unique_name

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
        self.project_id = None
        self.team_id = None
        self.session = None

    def __str__(self):
        return '<Dataset {!r}>'.format(self.name)

    @property
    def property_templates(self) -> PropertyTemplateCollection:
        """Return a resource representing all property templates in this dataset."""
        return PropertyTemplateCollection(team_id=self.team_id, dataset_id=self.uid,
                                          session=self.session, project_id=self.project_id)

    @property
    def condition_templates(self) -> ConditionTemplateCollection:
        """Return a resource representing all condition templates in this dataset."""
        return ConditionTemplateCollection(team_id=self.team_id, dataset_id=self.uid,
                                           session=self.session, project_id=self.project_id)

    @property
    def parameter_templates(self) -> ParameterTemplateCollection:
        """Return a resource representing all parameter templates in this dataset."""
        return ParameterTemplateCollection(team_id=self.team_id, dataset_id=self.uid,
                                           session=self.session, project_id=self.project_id)

    @property
    def material_templates(self) -> MaterialTemplateCollection:
        """Return a resource representing all material templates in this dataset."""
        return MaterialTemplateCollection(team_id=self.team_id, dataset_id=self.uid,
                                          session=self.session, project_id=self.project_id)

    @property
    def measurement_templates(self) -> MeasurementTemplateCollection:
        """Return a resource representing all measurement templates in this dataset."""
        return MeasurementTemplateCollection(team_id=self.team_id, dataset_id=self.uid,
                                             session=self.session, project_id=self.project_id)

    @property
    def process_templates(self) -> ProcessTemplateCollection:
        """Return a resource representing all process templates in this dataset."""
        return ProcessTemplateCollection(team_id=self.team_id, dataset_id=self.uid,
                                         session=self.session, project_id=self.project_id)

    @property
    def process_runs(self) -> ProcessRunCollection:
        """Return a resource representing all process runs in this dataset."""
        return ProcessRunCollection(team_id=self.team_id, dataset_id=self.uid,
                                    session=self.session, project_id=self.project_id)

    @property
    def measurement_runs(self) -> MeasurementRunCollection:
        """Return a resource representing all measurement runs in this dataset."""
        return MeasurementRunCollection(team_id=self.team_id, dataset_id=self.uid,
                                        session=self.session, project_id=self.project_id)

    @property
    def material_runs(self) -> MaterialRunCollection:
        """Return a resource representing all material runs in this dataset."""
        return MaterialRunCollection(team_id=self.team_id, dataset_id=self.uid,
                                     session=self.session, project_id=self.project_id)

    @property
    def ingredient_runs(self) -> IngredientRunCollection:
        """Return a resource representing all ingredient runs in this dataset."""
        return IngredientRunCollection(team_id=self.team_id, dataset_id=self.uid,
                                       session=self.session, project_id=self.project_id)

    @property
    def process_specs(self) -> ProcessSpecCollection:
        """Return a resource representing all process specs in this dataset."""
        return ProcessSpecCollection(team_id=self.team_id, dataset_id=self.uid,
                                     session=self.session, project_id=self.project_id)

    @property
    def measurement_specs(self) -> MeasurementSpecCollection:
        """Return a resource representing all measurement specs in this dataset."""
        return MeasurementSpecCollection(team_id=self.team_id, dataset_id=self.uid,
                                         session=self.session, project_id=self.project_id)

    @property
    def material_specs(self) -> MaterialSpecCollection:
        """Return a resource representing all material specs in this dataset."""
        return MaterialSpecCollection(team_id=self.team_id, dataset_id=self.uid,
                                      session=self.session, project_id=self.project_id)

    @property
    def ingredient_specs(self) -> IngredientSpecCollection:
        """Return a resource representing all ingredient specs in this dataset."""
        return IngredientSpecCollection(team_id=self.team_id, dataset_id=self.uid,
                                        session=self.session, project_id=self.project_id)

    @property
    def gemd(self) -> GEMDResourceCollection:
        """Return a resource representing all GEMD objects/templates in this dataset."""
        return GEMDResourceCollection(team_id=self.team_id, dataset_id=self.uid,
                                      session=self.session, project_id=self.project_id)

    @property
    def files(self) -> FileCollection:
        """Return a resource representing all files in the dataset."""
        return FileCollection(team_id=self.team_id, dataset_id=self.uid,
                              session=self.session, project_id=self.project_id)

    @property
    def ingestions(self) -> IngestionCollection:
        """Return a resource representing all files in the dataset."""
        return IngestionCollection(team_id=self.team_id, dataset_id=self.uid,
                                   session=self.session, project_id=self.project_id)

    def register(self, model: DataConcepts, *, dry_run=False) -> DataConcepts:
        """Register a data model object to the appropriate collection."""
        return self.gemd._collection_for(model).register(model, dry_run=dry_run)

    def register_all(self,
                     models: Iterable[DataConcepts],
                     *,
                     dry_run: bool = False,
                     status_bar: bool = False,
                     include_nested: bool = False) -> List[DataConcepts]:
        """
        Register multiple GEMD objects to each of their appropriate collections.

        Does so in an order that is guaranteed to store all linked items before the item that
        references them.

        If the GEMD objects have no UIDs, Citrine IDs will be assigned to them prior to passing
        them on to the server.  This is required as otherwise there is no way to determine how
        objects are related to each other.  When the registered objects are returned from the
        server, the input GEMD objects will be updated with whichever uids & _citr_auto:: tags are
        on the returned objects.  This means GEMD objects that already exist on the server will
        be updated with all their on-platform uids and tags.

        Parameters
        ----------
        models: Iterable[DataConcepts]
            The data model objects to register. Can be different types.

        dry_run: bool
            Whether to actually register the item or run a dry run of the register operation.
            Dry run is intended to be used for validation. Default: false

        status_bar: bool
            Whether to display a status bar using the tqdm module to track progress in
            registration. Requires installing the optional tqdm module. Default: false

        include_nested: bool
            Whether to just register the objects passed in the list, or include nested objects
            (e.g., obj.process, obj.spec.template, ...).  Default: false

        Returns
        -------
        List[DataConcepts]
            The registered versions

        """
        return self.gemd.register_all(
            models,
            dry_run=dry_run,
            status_bar=status_bar,
            include_nested=include_nested
        )

    def update(self, model: DataConcepts) -> DataConcepts:
        """Update a data model object using the appropriate collection."""
        return self.gemd._collection_for(model).update(model)

    def delete(self, uid: Union[UUID, str, LinkByUID, DataConcepts], *, dry_run=False):
        """
        Delete a GEMD resource from the appropriate collection.

        Parameters
        ----------
        uid: Union[UUID, str, LinkByUID, DataConcepts]
            A representation of the resource to delete (Citrine id, LinkByUID, or the object)
        dry_run: bool
            Whether to actually delete the item or run a dry run of the delete operation.
            Dry run is intended to be used for validation. Default: false

        """
        if isinstance(uid, DataConcepts):
            collection = self.gemd._collection_for(uid)
        else:
            collection = self.gemd
        return collection.delete(uid=uid, dry_run=dry_run)

    def delete_contents(
            self,
            *,
            prompt_to_confirm: bool = True,
            remove_templates: bool = True,
            timeout: float = 2 * 60,
            polling_delay: float = 1.0
    ):
        """
        Delete all the GEMD objects from within a single Dataset.

        Parameters
        ----------
        prompt_to_confirm: bool
            If True, prompt for user confirmation before triggering delete.  Included
            so that a script can skip confirmation if desired, but a user will not
            accidentally stumble in a notebook or other REPL environment.  Default: True
        remove_templates: bool
            If False, templates will not be deleted along with other contents of the
            dataset.  If true, all GEMD entities including templates will be deleted.
            Default: True
        timeout: float
            Amount of time to wait on the job (in seconds) before giving up.
            Note that this number has no effect on the underlying job itself,
            which can also time out server-side.
        polling_delay: float
            How long to delay between each polling retry attempt.
        Returns
        -------
        List[Tuple[LinkByUID, ApiError]]
            A list of (LinkByUID, api_error) for each failure to delete an object.
            Note that this method doesn't raise an exception if an object fails to be
            deleted.

        """
        path = format_escaped_url('teams/{team_id}/datasets/{dataset_uid}/contents',
                                  dataset_uid=self.uid,
                                  team_id=self.team_id)

        while prompt_to_confirm:
            print(f"Confirm you want to delete the contents of "
                  f"Dataset {self.name} {self.uid} [Y/N]")
            user_response = input()
            if user_response.lower() in {'y', 'yes'}:
                break  # return to main flow
            elif user_response.lower() in {'n', 'no'}:
                raise RuntimeError("delete_contents was invoked unintentionally")
            else:
                print(f'"{user_response}" is not a valid response')

        params = {"remove_templates": remove_templates}
        response = self.session.delete_resource(path, params=params)
        job_id = response["job_id"]

        return _poll_for_async_batch_delete_result(team_id=self.team_id,
                                                   session=self.session,
                                                   job_id=job_id,
                                                   timeout=timeout,
                                                   polling_delay=polling_delay)

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

        All data objects must be associated with this dataset resource. You must also
        have write access on this dataset.

        If you wish to delete more than 50 objects, queuing of deletes requires that
        the types of objects be known, and thus you _must_ provide ids in the form
        of BaseEntities.

        Also note that Attribute Templates cannot be deleted at present.

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
            How long to delay between each polling retry attempt.

        Returns
        -------
        List[Tuple[LinkByUID, ApiError]]
            A list of (LinkByUID, api_error) for each failure to delete an object.
            Note that this method doesn't raise an exception if an object fails to be
            deleted.

        """
        return self.gemd.batch_delete(id_list=id_list,
                                      timeout=timeout,
                                      polling_delay=polling_delay)


class DatasetCollection(Collection[Dataset]):
    """
    Represents the collection of all datasets associated with a project.

    Parameters
    ----------
    team_id: UUID
        Unique ID of the team this dataset collection belongs to.
    session: Session
        The Citrine session used to connect to the database.

    """

    _individual_key = None
    _collection_key = None
    _resource = Dataset

    def __init__(self,
                 *args,
                 session: Session = None,
                 team_id: UUID = None,
                 project_id: Optional[UUID] = None):
        # Handle positional arguments for backward compatibility
        args = _pad_positional_args(args, 2)
        self.project_id = project_id or args[0]
        self.session = session or args[1]
        if self.session is None:
            raise TypeError("Missing one required argument: session.")

        self.team_id = _data_manager_deprecation_checks(
            session=self.session,
            project_id=self.project_id,
            team_id=team_id,
            obj_type="Datasets")

    # After the Data Manager deprecation
    # this can be a Class Variable using the `teams/...` endpoint
    @property
    def _path_template(self):
        if self.project_id is None:
            return f'teams/{self.team_id}/datasets'
        else:
            return f'projects/{self.project_id}/datasets'

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
        dataset.team_id = self.team_id
        dataset.session = self.session
        dataset.project_id = self.project_id
        return dataset

    def register(self, model: Dataset) -> Dataset:
        """
        Create a new dataset in the collection, or update an existing one.

        If the Dataset has an ID present, then we update the existing resource,
        else we create a new one.

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

        # Only use the idempotent put approach if a) a unique name is provided, and b)
        # the session is configured to use it (default to False for backwards compatibility).
        if model.unique_name is not None and self.session.use_idempotent_dataset_put:
            # Leverage the create-or-update endpoint if we've got a unique name
            data = self.session.put_resource(path, scrub_none(dumped_dataset))
        else:

            if model.uid is None:
                # POST to create a new one if a UID is not assigned
                data = self.session.post_resource(path, scrub_none(dumped_dataset))

            else:
                # Otherwise PUT to update it
                data = self.session.put_resource(
                    self._get_path(model.uid), scrub_none(dumped_dataset))

        full_model = self.build(data)
        full_model.team_id = self.team_id
        return full_model

    def list(self, *, per_page: int = 1000) -> Iterator[Dataset]:
        """
        List datasets using pagination.

        Leaving page and per_page as default values will yield all elements in the
        collection, paginating over all available pages.

        Parameters
        ---------
        per_page: int, optional
            Max number of results to return per page. Default is 1000.  This parameter
            is used when making requests to the backend service.  If the page parameter
            is specified it limits the maximum number of elements in the response.

        Returns
        -------
        Iterator[Dataset]
            Datasets in this collection.

        """
        return super().list(per_page=per_page)

    def get_by_unique_name(self, unique_name: str) -> Dataset:
        """Get a Dataset with the given unique name."""
        if unique_name is None:
            raise ValueError("You must supply a unique_name")
        path = self._get_path(query_terms={"unique_name": unique_name})
        data = self.session.get_resource(path)

        if len(data) == 1:
            return self.build(data[0])
        elif len(data) > 1:
            raise RuntimeError("Received multiple results when requesting a unique dataset")
        else:
            raise NotFound(path)
