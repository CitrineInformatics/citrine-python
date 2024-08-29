"""Top-level class for all data concepts objects and collections thereof."""
import re
from abc import abstractmethod, ABC
from typing import TypeVar, Type, List, Union, Optional, Iterator, Iterable
from uuid import UUID, uuid4

from gemd.entity.dict_serializable import DictSerializable, DictSerializableMeta
from gemd.entity.base_entity import BaseEntity
from gemd.entity.link_by_uid import LinkByUID
from gemd.json import GEMDJson
from gemd.util import recursive_foreach, set_uuids

from citrine._rest.collection import Collection
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.properties import String, Mapping, Object
from citrine._serialization.properties import Optional as PropertyOptional
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.properties import UUID as PropertyUUID
from citrine._serialization.serializable import Serializable
from citrine._session import Session
from citrine._utils.functions import _data_manager_deprecation_checks, format_escaped_url, \
    _pad_positional_args, replace_objects_with_links, scrub_none
from citrine.exceptions import BadRequest
from citrine.jobs.job import _poll_for_job_completion
from citrine.resources.audit_info import AuditInfo
from citrine.resources.response import Response

CITRINE_SCOPE = 'id'
CITRINE_TAG_PREFIX = 'citr_auto'


class DataConceptsMeta(DictSerializableMeta):
    """Data Concepts metaclass for handling serialization."""

    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        resolved = next((b.typ for b in cls.__bases__ if getattr(b, "typ", None) is not None),
                        None)
        if resolved is not None:
            cls._typ_stash = resolved
        cls.typ = String("type")


class DataConcepts(
    PolymorphicSerializable['DataConcepts'],
    BaseEntity,
    metaclass=DataConceptsMeta
):
    """
    An abstract data concepts object.

    DataConcepts must be extended along with `Resource`.

    Parameters
    ----------
    typ: str
        A string denoting what type of DataConcepts class a particular instantiation is.

    """

    """Properties inherited from GEMD Base Entitiy."""
    uids = PropertyOptional(Mapping(String('scope'), String('id')), 'uids', override=True)
    tags = PropertyOptional(PropertyList(String()), 'tags', override=True)

    _type_key = "type"
    """str: key used to determine type of serialized object."""

    collection_dict = dict()
    """
    Dict[str, class]: dictionary from the type key to the associated collection \
     for every class that extends DataConcepts.

    Only populated if the :func:`get_collection_type` method is invoked.
    """

    """
    Fields that are added to the gemd data objects when they are used in this client

    * audit_info contains who/when information about the resource on the citrine platform
    * dataset is the unique Citrine id of the dataset that owns this resource
    """
    _audit_info = PropertyOptional(Object(AuditInfo), "audit_info", serializable=False)
    _dataset = PropertyOptional(PropertyUUID, "dataset", serializable=False)

    def __init__(self):
        self.typ = self._typ_stash

    @property
    def audit_info(self) -> Optional[AuditInfo]:
        """Get the audit info object."""
        return self._audit_info

    @property
    def uid(self) -> Optional[UUID]:
        """Get the Citrine Identifier (scope = "id"), or None if not registered."""
        return self.uids.get(CITRINE_SCOPE)

    @property
    def dataset(self) -> Optional[UUID]:
        """Get the dataset of this object, if it was returned by the backend."""
        return self._dataset

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """
        Determine the class of a serialized object.

        The data dictionary must have a 'type' key whose value corresponds to the response key
        of one of the classes that extends :class:`DataConcepts`.

        Parameters
        ----------
        data: dict
            A dictionary corresponding to a serialized data concepts object of unknown type.
            This method will also work if data is a deserialized GEMD object.

        Returns
        -------
        class
            The class corresponding to data.

        """
        if isinstance(data, DictSerializable):
            data = data.as_dict()
        return DictSerializable.class_mapping[data['type']]

    @classmethod
    def get_collection_type(cls, data) -> "Type[DataConceptsCollection]":
        """
        Determine the associated collection type for a serialized data object.

        The data dictionary must have a 'type' key whose value corresponds to the individual key
        of one of the collections that extends :class:`DataConceptsCollection`.

        Parameters
        ----------
        data: dict
            A dictionary corresponding to a serialized data concepts object of unknown type.
            This method will also work if data is a deserialized GEMD object.

        Returns
        -------
        collection
            The collection type corresponding to data.

        """
        if len(DataConcepts.collection_dict) == 0:
            # This branch is intended to populate collection dict on first call
            DataConcepts._make_collection_dict()
        if isinstance(data, DictSerializable):
            data = data.as_dict()
        return DataConcepts.collection_dict[data['type']]

    @staticmethod
    def _make_collection_dict():
        """Construct a dictionary from each type key to the associated collection."""
        from citrine.resources.condition_template import ConditionTemplateCollection
        from citrine.resources.parameter_template import ParameterTemplateCollection
        from citrine.resources.property_template import PropertyTemplateCollection
        from citrine.resources.material_template import MaterialTemplateCollection
        from citrine.resources.measurement_template import MeasurementTemplateCollection
        from citrine.resources.process_template import ProcessTemplateCollection
        from citrine.resources.ingredient_spec import IngredientSpecCollection
        from citrine.resources.material_spec import MaterialSpecCollection
        from citrine.resources.measurement_spec import MeasurementSpecCollection
        from citrine.resources.process_spec import ProcessSpecCollection
        from citrine.resources.ingredient_run import IngredientRunCollection
        from citrine.resources.material_run import MaterialRunCollection
        from citrine.resources.measurement_run import MeasurementRunCollection
        from citrine.resources.process_run import ProcessRunCollection
        _collection_list = [
            ConditionTemplateCollection, ParameterTemplateCollection, PropertyTemplateCollection,
            MaterialTemplateCollection, MeasurementTemplateCollection, ProcessTemplateCollection,
            IngredientSpecCollection, MaterialSpecCollection, MeasurementSpecCollection,
            ProcessSpecCollection, IngredientRunCollection, MaterialRunCollection,
            MeasurementRunCollection, ProcessRunCollection
        ]
        for collection in _collection_list:
            DataConcepts.collection_dict[collection._individual_key] = collection


def _make_link_by_uid(gemd_object_rep: Union[str, UUID, BaseEntity, LinkByUID]) -> LinkByUID:
    if isinstance(gemd_object_rep, BaseEntity):
        return gemd_object_rep.to_link(CITRINE_SCOPE, allow_fallback=True)
    elif isinstance(gemd_object_rep, LinkByUID):
        return gemd_object_rep
    elif isinstance(gemd_object_rep, (str, UUID)):
        uid = str(gemd_object_rep)
        scope = CITRINE_SCOPE
        return LinkByUID(scope, uid)
    else:
        raise TypeError("Link can only be created from a GEMD object, LinkByUID, str, or UUID."
                        "Instead got {}.".format(gemd_object_rep))


ResourceType = TypeVar('ResourceType', bound='DataConcepts')


class DataConceptsCollection(Collection[ResourceType], ABC):
    """
    A collection of one kind of data concepts object.

    Parameters
    ----------
    team_id: UUID
        The uid of the team that this collection belongs to.
    dataset_id: UUID
        The uid of the dataset that this collection belongs to. If None then the collection
        ranges over all datasets in the team. Note that this is only allowed for certain
        actions. For example, you can use :func:`list_by_tag` to search over all datasets,
        but when using :func:`register` to upload or update an object, a dataset must be specified.
    session: Session
        The Citrine session used to connect to the database.

    """

    def __init__(self,
                 *args,
                 session: Session = None,
                 dataset_id: Optional[UUID] = None,
                 team_id: UUID = None,
                 project_id: Optional[UUID] = None):
        # Handle positional arguments for backward compatibility
        args = _pad_positional_args(args, 3)
        self.project_id = project_id or args[0]
        self.dataset_id = dataset_id or args[1]
        self.session = session or args[2]
        if self.session is None:
            raise TypeError("Missing one required argument: session.")

        self.team_id = _data_manager_deprecation_checks(
            session=self.session,
            project_id=self.project_id,
            team_id=team_id,
            obj_type="GEMD Objects")

    @classmethod
    @abstractmethod
    def get_type(cls) -> Type[Serializable]:
        """Return the resource type in the collection."""

    @property
    def _path_template(self):
        collection_key = self._collection_key.replace("_", "-")
        return f'teams/{self.team_id}/datasets/{self.dataset_id}/{collection_key}'

    # After Data Manager deprecation, both can use the `teams/...` path.
    @property
    def _dataset_agnostic_path_template(self):
        if self.project_id is None:
            return f'teams/{self.team_id}/{self._collection_key.replace("_", "-")}'
        else:
            return f'projects/{self.project_id}/{self._collection_key.replace("_", "-")}'

    def build(self, data: dict) -> ResourceType:
        """
        Build an object of type ResourceType from a serialized dictionary.

        This is an internal method, and should not be called directly by users.

        Parameters
        ----------
        data: dict
            A serialized data model object.

        Returns
        -------
        ResourceType
            A data model object built from the dictionary.

        """
        return self.get_type().build(data)

    def list(self, *,
             per_page: Optional[int] = 100,
             forward: bool = True) -> Iterator[ResourceType]:
        """
        Get all visible elements of the collection.

        The order of results should not be relied upon, but for now they are sorted by
        dataset, object type, and creation time (in that order of priority).

        Parameters
        ---------
        per_page: int, optional
            Max number of results to return per page. It is very unlikely that
            setting this parameter to something other than the default is useful.
            It exists for rare situations where the client is bandwidth constrained
            or experiencing latency from large payload sizes.
        forward: bool
            Set to False to reverse the order of results (i.e., return in descending order)

        Returns
        -------
        Iterator[ResourceType]
            Every object in this collection.

        """
        params = {}
        if self.dataset_id is not None:
            params['dataset_id'] = str(self.dataset_id)
        raw_objects = self.session.cursor_paged_resource(
            self.session.get_resource,
            self._get_path(ignore_dataset=True),
            forward=forward,
            per_page=per_page,
            params=params)
        return (self.build(raw) for raw in raw_objects)

    def register(self, model: ResourceType, *, dry_run=False):
        """
        Create a new element of the collection or update an existing element.

        If the input model has an ID that corresponds to an existing object in the
        database, then that object will be updated. Otherwise a new object will be created.

        Only the top-level object in `model` itself is written to the database with this
        method. References to other objects are persisted as links, and the object returned
        by this method has all instances of data objects replaced by instances of LinkByUid.
        Registering an object which references other objects does NOT implicitly register
        those other objects. Rather, those other objects' values are ignored, and the
        pre-existence of objects with their IDs is asserted before attempting to write
        `model`.

        Parameters
        ----------
        model: ResourceType
            The DataConcepts object.
        dry_run: bool
            Whether to actually register the item or run a dry run of the register operation.
            Dry run is intended to be used for validation. Default: false

        Returns
        -------
        ResourceType
            A copy of the registered object as it now exists in the database.

        """
        if self.dataset_id is None:
            raise RuntimeError("Must specify a dataset in order to register a data model object.")
        path = self._get_path()
        params = {'dry_run': dry_run}

        temp_scope = str(uuid4())
        scope = temp_scope if dry_run else CITRINE_SCOPE
        set_uuids(model, scope=scope)
        dumped_data = replace_objects_with_links(scrub_none(model.dump()))

        data = self.session.post_resource(path, dumped_data, params=params)
        registered = self.build(data)

        recursive_foreach(model, lambda x: x.uids.pop(temp_scope, None))  # Strip temp uids
        if not dry_run:
            # Platform may add a CITRINE_SCOPE uid and citr_auto tags; update locals
            model.uids.update({k: v for k, v in registered.uids.items()})
            if registered.tags is not None:
                if model.tags is None:  # This is somehow hit by nextgen-devkit tests
                    model.tags = list()  # pragma: no cover
                model.tags.extend([tag for tag in registered.tags
                                   if re.match(f"^{CITRINE_TAG_PREFIX}::", tag)])
        else:
            # Remove of the tags/uids the platform spuriously added
            # this might leave objects with just the temp ids, which we want to strip later
            if CITRINE_SCOPE not in model.uids:
                registered.uids.pop(CITRINE_SCOPE, None)
            if registered.tags is not None:
                todo = [tag for tag in registered.tags
                        if re.match(f"^{CITRINE_TAG_PREFIX}::", tag)]
                for tag in todo:  # Covering this block would require dark art
                    if tag not in model.tags:
                        registered.tags.remove(tag)
        return registered

    def register_all(self,
                     models: Iterable[ResourceType],
                     *,
                     dry_run: bool = False,
                     status_bar: bool = False,
                     include_nested: bool = False) -> List[ResourceType]:
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

        This method has the same behavior as `register`, except that no models will be
        written if any one of them is invalid.  Using this method should yield significant
        improvements to write speed over separate calls to `register`.

        Parameters
        ----------
        models: Iterable[DataConcepts]
            The data model objects to register. Can be different types.

        dry_run: bool
            Whether to actually register the objects or run a dry run of the register operation.
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
            Each object model as it now exists in the database.

        """
        # avoiding a circular import
        from citrine.resources.gemd_resource import GEMDResourceCollection
        gemd_collection = GEMDResourceCollection(team_id=self.team_id,
                                                 dataset_id=self.dataset_id,
                                                 session=self.session)
        return gemd_collection.register_all(
            models,
            dry_run=dry_run,
            status_bar=status_bar,
            include_nested=include_nested
        )

    def update(self, model: ResourceType) -> ResourceType:
        """
        Update a data object model.

        Update a particular element of the collection,
        first attempting a simple update using register and falling back to async_update
        if the changes require it (e.g., updating template bounds).

        model: ResourceType
            The DataConcepts object.
        """
        try:
            return self.register(model, dry_run=False)
        except BadRequest:
            # If register() cannot be used because an asynchronous check is required
            return self.async_update(model, dry_run=False,
                                     wait_for_response=True, return_model=True)

    def async_update(self, model: ResourceType, *,
                     dry_run: bool = False,
                     wait_for_response: bool = True,
                     timeout: float = 2 * 60,
                     polling_delay: float = 1.0,
                     return_model: bool = False) -> Optional[Union[UUID, ResourceType]]:
        """
        Update a particular element of the collection with data validation.

        Update a particular element of the collection, doing a deeper check to ensure that
        the dependent data objects are still with the (potentially) changed constraints
        of this change. This will allow you to make bounds and allowed named/labels changes
        to templates.

        Parameters
        ----------
        model: ResourceType
            The DataConcepts object.
        dry_run: bool
            Whether to actually update the item or run a dry run of the update operation.
            Dry run is intended to be used for validation. Default: false
        wait_for_response: bool
            Whether to poll for the eventual response. This changes the return type (see
            below).
        timeout: float
            How long to poll for the result before giving up. This is expressed in
            (fractional) seconds.
        polling_delay: float
            How long to delay between each polling retry attempt.
        return_model: bool
            Whether or not to return an updated version of the resource
            If wait_for_response is False, then this argument has no effect

        Returns
        -------
        Optional[UUID]
            If wait_for_response if True, then this call will poll the backend, waiting
            for the eventual job result. In the case of successful validation/update,
            a return value of None is provided unless return_model is True, in which case
            the updated resource is fetched and returned. In the case of a failure
            validating or processing the update, an exception (JobFailureError) is raised
            and an error message is logged with the underlying reason of the failure.

            If wait_for_response if False, A job ID (of type UUID) is returned that one
            can use to poll for the job completion and result with the
            :func:`~citrine.resources.DataConceptsCollection.poll_async_update_job`
            method.

        """
        temp_scope = str(uuid4())
        GEMDJson(scope=temp_scope).dumps(model)  # This apparent no-op populates uids
        dumped_data = replace_objects_with_links(scrub_none(model.dump()))
        recursive_foreach(model, lambda x: x.uids.pop(temp_scope, None))  # Strip temp uids

        scope = CITRINE_SCOPE
        id = dumped_data['uids'][scope]
        if self.dataset_id is None:
            raise RuntimeError("Must specify a dataset in order to update "
                               "a data model object with data validation.")

        url = self._get_path(action=[scope, id, "async"])
        response_json = self.session.put_resource(url, dumped_data, params={'dry_run': dry_run})

        job_id = response_json["job_id"]

        if wait_for_response:
            self.poll_async_update_job(job_id=job_id, timeout=timeout,
                                       polling_delay=polling_delay)

            # That worked, return nothing or return the object
            if return_model:
                return self.get(LinkByUID(scope=scope, id=id))
            else:
                return None
        else:
            # TODO: use JobSubmissionResponse here instead
            return job_id

    def poll_async_update_job(self, job_id: UUID, *, timeout: float = 2 * 60,
                              polling_delay: float = 1.0) -> None:
        """
        Poll for the result of the async_update call.

        This call will poll the backend given the Job ID that came from a call to
        :func:`~citrine.resources.DataConceptsCollection.async_update`,
        waiting for the eventual job result. In the case of successful validation/update,
        a return value of None is provided which indicates success. In the case of
        a failure validating or processing the update, an exception (JobFailureError)
        is raised and an error message is logged with the underlying reason of the
        failure.

        Parameters
        ----------
        job_id: UUID
           The job ID for the asynchronous update job we wish to poll.
        timeout:
            How long to poll for the result before giving up. This is expressed in
            (fractional) seconds.
        polling_delay:
            How long to delay between each polling retry attempt.

        Returns
        -------
        None
           This method will raise an appropriate exception if the job failed, else
           it will return None to indicate the job was successful.

        """
        # Poll for job completion - this will raise an error if the job failed
        _poll_for_job_completion(
            session=self.session,
            team_id=self.team_id,
            job=job_id, timeout=timeout,
            polling_delay=polling_delay)

        # That worked, nothing returned in this case
        return None

    def get(self, uid: Union[UUID, str, LinkByUID, BaseEntity]) -> ResourceType:
        """
        Get an element of the collection by its id.

        Parameters
        ----------
        uid: Union[UUID, str, LinkByUID, BaseEntity]
            A representation of the object (Citrine id, LinkByUID, or the object itself)

        Returns
        -------
        ResourceType
            An object with specified scope and uid

        """
        link = _make_link_by_uid(uid)
        path = self._get_path(ignore_dataset=self.dataset_id is None, action=[link.scope, link.id])
        data = self.session.get_resource(path)
        return self.build(data)

    def list_by_name(self, name: str, *, exact: bool = False,
                     forward: bool = True, per_page: int = 100) -> Iterator[ResourceType]:
        """
        Get all objects with specified name in this dataset.

        Parameters
        ----------
        name: str
            case-insensitive object name prefix to search.
        exact: bool
            Set to True to change prefix search to exact search (but still case-insensitive).
            Default is False.
        forward: bool
            Set to False to reverse the order of results (i.e., return in descending order).
        per_page: int
            Controls the number of results fetched with each http request to the backend.
            Typically, this is set to a sensible default and should not be modified. Consider
            modifying this value only if you find this method is unacceptably latent.

        Returns
        -------
        Iterator[ResourceType]
            List of every object in this collection whose `name` matches the search term.

        """
        if self.dataset_id is None:
            raise RuntimeError("Must specify a dataset to filter by name.")
        params = {'dataset_id': str(self.dataset_id), 'name': name, 'exact': exact}
        raw_objects = self.session.cursor_paged_resource(
            self.session.get_resource,
            # "Ignoring" dataset because it is in the query params (and required)
            self._get_path(ignore_dataset=True, action="filter-by-name"),
            forward=forward,
            per_page=per_page,
            params=params)
        return (self.build(raw) for raw in raw_objects)

    def list_by_tag(self, tag: str, *, per_page: int = 100) -> Iterator[ResourceType]:
        """
        Get all objects bearing a tag prefixed with `tag` in the collection.

        The order of results is largely not meaningful. Results from the same dataset will be
        grouped together but no other meaningful ordering can be relied upon. Duplication in
        the result set may (but needn't) occur when one object has multiple tags matching the
        search tag. For this reason, it is inadvisable to put 2 tags with the same prefix
        (e.g., 'foo::bar' and 'foo::baz') in the same object when it can be avoided.

        Parameters
        ----------
        tag: str
            The prefix with which to search. Must fully match up to the first delimiter (ex.
            'foo' and 'foo::b' both match 'foo::bar' but 'fo' is insufficient.
        per_page: int
            Controls the number of results fetched with each http request to the backend.
            Typically, this is set to a sensible default and should not be modified. Consider
            modifying this value only if you find this method is unacceptably latent.

        Returns
        -------
        Iterator[ResourceType]
            Every object in this collection.

        """
        params = {'tags': [tag]}
        if self.dataset_id is not None:
            params['dataset_id'] = str(self.dataset_id)
        raw_objects = self.session.cursor_paged_resource(
            self.session.get_resource,
            self._get_path(ignore_dataset=True),
            per_page=per_page,
            params=params)
        return (self.build(raw) for raw in raw_objects)

    def delete(self, uid: Union[UUID, str, LinkByUID, BaseEntity], *, dry_run: bool = False):
        """
        Delete an element of the collection by its id.

        Parameters
        ----------
        uid: Union[UUID, str, LinkByUID, BaseEntity]
            A representation of the object (Citrine id, LinkByUID, or the object itself)
        dry_run: bool
            Whether to actually delete the item or run a dry run of the delete operation.
            Dry run is intended to be used for validation. Default: false

        """
        link = _make_link_by_uid(uid)
        path = self._get_path(action=[link.scope, link.id])
        params = {'dry_run': dry_run}
        self.session.delete_resource(path, params=params)
        return Response(status_code=200)  # delete succeeded

    def _get_relation(self, relation: str, uid: Union[UUID, str, LinkByUID, BaseEntity],
                      forward: bool = True, per_page: int = 100) -> Iterator[ResourceType]:
        """
        Generic method for searching this collection by relation to another object.

        Parameters
        ----------
        relation
            Reflects the type of the object with the provided uid and scope, e.g.,
            'process-templates' if searching for process specs by process template.
        uid
            A representation of the object upon which this search is based, e.g., a
            Citrine ID of a process template whose process spec usages are being located.
        forward
            Whether to pages results in ascending order. Typically this is an
            unnecessary parameter.
        per_page
            The number of results to retrieve in each request to the backend. Typically
            this is an unnecessary parameter.
        Returns
        -------
        Iterator[ResourceType]
            Objects in this collection which are somehow related to the object with
            provided uid and scope.

        """
        params = {}
        if self.dataset_id is not None:
            params['dataset_id'] = str(self.dataset_id)
        link = _make_link_by_uid(uid)
        raw_objects = self.session.cursor_paged_resource(
            self.session.get_resource,
            format_escaped_url('teams/{}/{}/{}/{}/{}',
                               self.team_id,
                               relation,
                               link.scope,
                               link.id,
                               self._collection_key.replace('_', '-')
                               ),
            forward=forward,
            per_page=per_page,
            params=params,
            version='v1')
        return (self.build(raw) for raw in raw_objects)
